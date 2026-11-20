import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    # Database (PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Celery / Redis
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Flask-RESTX (API docs)
    RESTX_MASK_SWAGGER = False

    # Frontend folder (backend ke bahar, backend ke bilkul sath)
    FRONTEND_DIR = os.path.abspath(os.path.join(basedir, "..", "frontend"))
        # Celery settings (Flask-Celery integration isi dictionary ko use karta hai)
    CELERY = dict(
        broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        task_track_started=True,
        result_expires=3600,
        broker_connection_retry_on_startup=True,
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}