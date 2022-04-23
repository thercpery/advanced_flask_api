from flask_restful import Resource, reqparse
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from werkzeug.security import safe_str_cmp
from models.user import UserModel
from blocklist import BLOCKLIST

# "_" before variable names are private variables that should not be imported anywhere else in Python.

BLANK_ERROR = "'{}' cannot be blank"
USER_ALREADY_EXISTS = "A user with that username already exists."
CREATED_SUCCESSFULLY = "User created successfully."
USER_NOT_FOUND = "User not found."
USER_DELETED = "User deleted."
INVALID_CREDENTIALS = "Invalid credentials!"
USER_LOGGED_OUT = "user <id={user_id}> successfully logged out."

_user_parser = reqparse.RequestParser()
_user_parser.add_argument(
    "username", type=str, required=True, help=BLANK_ERROR.format("username")
)
_user_parser.add_argument(
    "password", type=str, required=True, help=BLANK_ERROR.format("password")
)


class UserRegister(Resource):
    @classmethod
    def post(cls):
        data = _user_parser.parse_args()

        if UserModel.find_by_username(data["username"]):
            return {"message": USER_ALREADY_EXISTS}, 400

        user = UserModel(**data)
        user.save_to_db()

        return {"message": CREATED_SUCCESSFULLY}, 201


class User(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        return user.json()

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
        1. Get the data from parser(request body).
        2. Find the user in the database.
        3. Check the password.
        4. Create an access token.
        5. Craete refresh token (will look at this later).
        6. Return the access token
        """

        # Get the data from parser
        data = _user_parser.parse_args()

        # Find the user in the DB
        user = UserModel.find_by_username(data["username"])

        # Check the password if correct
        # This is what the `authenticate()` function used to do.
        if user and safe_str_cmp(user.password, data["password"]):
            # Create access and refresh token
            # identity= is what the `identity()` function used to do.
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

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
