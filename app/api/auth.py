from flask_login import current_user, login_user, logout_user
from flask_restx import Namespace, Resource, fields

from app.models import User

ns = Namespace("auth", description="Login / logout")

login_input = ns.model("LoginInput", {
    "username": fields.String(required=True),
    "password": fields.String(required=True),
})


@ns.route("/login")
class Login(Resource):
    @ns.expect(login_input, validate=True)
    def post(self):
        """Admin login"""
        data = ns.payload
        user = User.query.filter_by(username=data["username"].strip().lower()).first()
        if not user or not user.check_password(data["password"]):
            return {"message": "Username ya password galat hai"}, 401
        login_user(user)
        return {"username": user.username}


@ns.route("/logout")
class Logout(Resource):
    def post(self):
        """Logout"""
        logout_user()
        return {"message": "Logout ho gaye"}


@ns.route("/me")
class Me(Resource):
    def get(self):
        """Abhi kaun login hai"""
        return {"username": current_user.username}