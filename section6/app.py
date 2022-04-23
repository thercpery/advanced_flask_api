import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_uploads import configure_uploads
from marshmallow import ValidationError
from ma import ma
from db import db
from resources.user import (UserRegister, User, UserLogin, UserLogout, TokenRefresh)
from resources.item import Item, ItemList
from resources.store import Store, StoreList
from resources.confirmation import Confirmation, ConfirmationByUser
from resources.image import ImageUpload
from libs.image_helper import IMAGE_SET
from models.user import UserModel
from models.item import ItemModel
from models.store import StoreModel
from models.confirmation import ConfirmationModel
from blocklist import BLOCKLIST

uri = os.getenv("DATABASE_URL") or "sqlite:///data.db"  # or other relevant config var
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

# Init app
app = Flask(__name__)
load_dotenv(".env", verbose=True)
app.config.from_object("default_config")
app.config.from_envvar("APPLICATION_SETTINGS")
configure_uploads(app, IMAGE_SET)
CORS(app)
# app.secret_key = "rc"
api = Api(app)
db.init_app(app)
ma.init_app(app)


# Create the DB
@app.before_first_request
def create_tables():
    UserModel.__table__.create(db.session.bind, checkfirst=True)
    StoreModel.__table__.create(db.session.bind, checkfirst=True)
    ItemModel.__table__.create(db.session.bind, checkfirst=True)
    ConfirmationModel.__table__.create(db.session.bind, checkfirst=True)


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):  # except ValidationError as err
    return jsonify(err.messages), 400


jwt = JWTManager(app)  # this will not create a new endpoint called "/auth"


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in BLOCKLIST


api.add_resource(Item, "/api/item/<string:name>")
api.add_resource(ItemList, "/api/items")
api.add_resource(Store, "/api/store/<string:name>")
api.add_resource(StoreList, "/api/stores")
api.add_resource(UserRegister, "/api/user/register")
api.add_resource(UserLogin, "/api/user/login")
api.add_resource(UserLogout, "/api/user/logout")
api.add_resource(User, "/api/user/<int:user_id>")
api.add_resource(TokenRefresh, "/refresh")
api.add_resource(Confirmation, "/api/user/confirm/<string:confirmation_id>")
api.add_resource(ConfirmationByUser, "/api/user/confirmations/<int:user_id>")
api.add_resource(ImageUpload, "/api/upload/image")

if __name__ == "__main__":
    app.run(port=6000, debug=True)
