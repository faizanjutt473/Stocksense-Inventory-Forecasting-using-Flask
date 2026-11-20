import os

import click
from flask import Flask, redirect, jsonify, send_from_directory, abort
from flask_login import current_user
from sqlalchemy import text
from celery import Celery, Task

from config import config
from .extensions import db, migrate, cors, login_manager

PAGES = {"dashboard", "products", "suppliers", "purchase-orders",
         "stock", "scanner", "forecast", "reports"}


def celery_init_app(app):
    """Celery ko Flask ke sath jodta hai (tasks ko app context milta hai)."""

    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app(config_name="default"):
    cfg = config[config_name]
    frontend_dir = cfg.FRONTEND_DIR

    # static_folder=None: pages hum khud serve karte hain (login check ke sath)
    app = Flask(__name__, static_folder=None)
    app.config.from_object(cfg)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    login_manager.init_app(app)

    # Models
    from . import models  # noqa: F401
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Celery aur uske tasks
    celery_init_app(app)
    from . import tasks  # noqa: F401

    # REST API
    from .api import api_bp
    app.register_blueprint(api_bp)

    # ---------- Frontend ----------
    @app.route("/css/<path:filename>")
    def css_files(filename):
        return send_from_directory(os.path.join(frontend_dir, "css"), filename)

    @app.route("/js/<path:filename>")
    def js_files(filename):
        return send_from_directory(os.path.join(frontend_dir, "js"), filename)

    @app.route("/<page>.html")
    def html_page(page):
        if page == "login":
            if current_user.is_authenticated:
                return redirect("/dashboard.html")
            return send_from_directory(frontend_dir, "login.html")
        if page in PAGES:
            if not current_user.is_authenticated:
                return redirect("/login.html")
            return send_from_directory(frontend_dir, page + ".html")
        abort(404)

    @app.route("/")
    def home():
        return redirect("/dashboard.html")

    @app.after_request
    def no_cache_for_html(resp):
        # Logout ke baad back button se purana page na khule
        if resp.mimetype == "text/html":
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify(status="ok", database="connected")
        except Exception as e:
            return jsonify(status="error", detail=str(e)), 500

    # ---------- Admin banane ki command ----------
    @app.cli.command("create-admin")
    @click.option("--username", prompt="Username")
    @click.password_option()
    def create_admin(username, password):
        """Admin user banata hai (ya password badalta hai)."""
        username = username.strip().lower()
        if len(username) < 3:
            raise click.ClickException("Username kam az kam 3 characters ka ho")
        if len(password) < 8:
            raise click.ClickException("Password kam az kam 8 characters ka ho")
        user = User.query.filter_by(username=username).first()
        if user:
            user.set_password(password)
            msg = "Password update ho gaya"
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            msg = "Admin ban gaya"
        db.session.commit()
        click.echo(msg)

    return app