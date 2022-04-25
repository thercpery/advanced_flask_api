import traceback

from flask_restful import Resource
from flask import request
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
from libs.strings import gettext
from libs.mailgun import MailgunException
from models.confirmation import ConfirmationModel

# "_" before variable names are private variables that should not be imported anywhere else in Python.

user_schema = UserSchema()


class UserRegister(Resource):
    @classmethod
    def post(cls):
        user = user_schema.load(request.get_json())

        if UserModel.find_by_username(user.username) and UserModel.find_by_email(user.email):
            return {"message": gettext("user_username_exists")}, 400

        try:
            user.save_to_db()
            confirmation = ConfirmationModel(user.id)
            confirmation.save_to_db()
            user.send_confirmation_email()
            return {"message": gettext("user_registered")}, 201
        except MailgunException as e:
            user.delete_to_db()  # rollback
            return {"message": str(e)}, 500
        except:
            traceback.print_exc()
            user.delete_to_db()
            return {"message": gettext("user_error_creating")}, 500


class User(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, 404
        return user_schema.dump(user), 200

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": gettext("user_not_found")}, 404
        user.delete_to_db()
        return {"message": gettext("user_deleted")}, 200


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
            confirmation = user.most_recent_confirmation
            if confirmation and confirmation.is_confirmed:
                access_token = create_access_token(identity=user.id, fresh=True)
                refresh_token = create_refresh_token(identity=user.id)
                return {"access_token": access_token, "refresh_token": refresh_token}, 200
            return {"message": gettext("user_not_confirmed").format(user.email)}, 400

        # If username not found and/or password is wrong.
        return {"message": gettext("user_invalid_credentials")}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required()
    def post(cls):
        user_id = get_jwt_identity()
        jti = get_jwt()["jti"]  # jti is a "JWT ID", a unique identifier for a JWT.
        BLOCKLIST.add(jti)
        return {"message": gettext("user_logged_out").format(user_id)}, 200


class TokenRefresh(Resource):
    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200

