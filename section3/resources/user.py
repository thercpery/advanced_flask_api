import traceback

from flask_restful import Resource
from flask import request, make_response, render_template, redirect
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from werkzeug.security import safe_str_cmp
from models.user import UserModel
from schemas.user import UserSchema
from blocklist import BLOCKLIST
from libs.mailgun import MailgunException

# "_" before variable names are private variables that should not be imported anywhere else in Python.

USER_ALREADY_EXISTS = "A user with that username or email already exists."
CREATED_SUCCESSFULLY = "User created successfully."
USER_NOT_FOUND = "User not found."
USER_DELETED = "User deleted."
INVALID_CREDENTIALS = "Invalid credentials!"
USER_LOGGED_OUT = "user <id={user_id}> successfully logged out."
NOT_CONFIRMED_ERROR = "You have not confirmed registration, please check your email <{}>."
FAILED_TO_CREATE = "Internal server error. Failed to create user."
SUCCESS_REGISTER_MESSAGE = "Account created successfully, and email with an activateion link has been sent to your email address. Please check."

user_schema = UserSchema()


class UserRegister(Resource):
    @classmethod
    def post(cls):
        user = user_schema.load(request.get_json())

        if UserModel.find_by_username(user.username) and UserModel.find_by_email(user.email):
            return {"message": USER_ALREADY_EXISTS}, 400

        try:
            user.save_to_db()
            user.send_confirmation_email()
            return {"message": CREATED_SUCCESSFULLY}, 201
        except MailgunException as e:
            user.delete_to_db()
            return {"message": str(e)}, 500
        except:
            traceback.print_exc()
            return {"message": FAILED_TO_CREATE}, 500


class User(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        return user_schema.dump(user), 200

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        user.delete_to_db()
        return {"message": USER_DELETED}, 200


class UserLogin(Resource):
    @classmethod
    def post(cls):
        """
        This authenticates the user manually
        1. Get the user_data from parser(request body).
        2. Find the user in the database.
        3. Check the password.
        4. Create an access token.
        5. Create refresh token (will look at this later).
        6. Return the access token
        """

        # Get the user_data from parser
        user_json = request.get_json()
        user_data = user_schema.load(user_json, partial=("email",))

        # Find the user in the DB
        user = UserModel.find_by_username(user_data.username)

        # Check the password if correct
        # This is what the `authenticate()` function used to do.
        if user and safe_str_cmp(user.password, user_data.password):
            # Create access and refresh token
            # identity= is what the `identity()` function used to do.
            if user.is_activated:
                access_token = create_access_token(identity=user.id, fresh=True)
                refresh_token = create_refresh_token(identity=user.id)
                return {"access_token": access_token, "refresh_token": refresh_token}, 200
            return {"message": NOT_CONFIRMED_ERROR.format(user.username)}, 400

        # If username not found and/or password is wrong.
        return {"message": INVALID_CREDENTIALS}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required()
    def post(cls):
        user_id = get_jwt_identity()
        jti = get_jwt()["jti"]  # jti is a "JWT ID", a unique identifier for a JWT.
        BLOCKLIST.add(jti)
        return {"message": USER_LOGGED_OUT.format(user_id=user_id)}, 200


class TokenRefresh(Resource):
    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200


class UserConfirm(Resource):
    """
    This confirms the user via email
    1. Find the user in the database.
    2. Return a message if not found.
    3. Activate the user via email.
    4. Update the user in the DB.
    5. Return true if user successfully confirmed.
    """
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 400

        user.is_activated = True
        user.save_to_db()
        # return redirect("/api/user/login", 302)  # used if there is a web app only
        headers = {"Content-Type": "text/html"}
        return make_response(render_template("confirmation_page.html", email=user.username), 200, headers)


