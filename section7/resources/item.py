from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required
from models.item import ItemModel
from schemas.item import ItemSchema
from libs.strings import gettext

NAME_ALREADY_EXISTS = "An item with name '{}' already exists."

item_schema = ItemSchema()
item_list_schema = ItemSchema(many=True)


class Item(Resource):
    """ Using instance methods. """
    # item = Item()
    # item.get()

    """ Using class methods """
    # Item.get()

    @classmethod
    @jwt_required()  # analogy: In Javascript terms, this is the "auth.verify"
    def get(cls, name: str):
        item = ItemModel.find_by_name(name)
        if item:
            # If item is found
            return item_schema.dump(item), 200
        # If item not found
        return {"message": gettext("item_not_found")}, 404

    @classmethod
    @jwt_required()  # analogy: In Javascript terms, this is the "auth.verify"
    def post(cls, name: str):  # /item/chair
        if ItemModel.find_by_name(name):
            # If item already exists return false
            return {"message": gettext("item_name_exists").format(name)}, 400

        item_json = request.get_json()  # price, store_id
        item_json["name"] = name
        item = item_schema.load(item_json)

        try:
            item.save_to_db()
        except:
            return {"message": gettext("item_error_inserting")}, 500

        return True, 201

    @classmethod
    @jwt_required()  # analogy: In Javascript terms, this is the "auth.verify"
    def delete(cls, name: str):
        item = ItemModel.find_by_name(name)

        if item:
            item.delete_from_db()
            return {"message": gettext("item_deleted")}, 201

        return {"message": gettext("item_not_found")}, 404

    @classmethod
    @jwt_required(
        fresh=False
    )  # analogy: In Javascript terms, this is the "auth.verify"
    def put(cls, name: str):
        item_json = request.get_json()
        item = ItemModel.find_by_name(name)

        if item is None:
            # If item does not exist create one.
            item_json["name"] = name
            item = item_schema.load(item_json)
        else:
            # If item exists update the existing item.
            item.price = item_json["price"]
            if item_json["store_id"]:
                item.store_id = item_json["store_id"]

        item.save_to_db()
        return True, 201


class ItemList(Resource):
    @classmethod
    def get(cls):
        return [item_list_schema.dump(ItemModel.find_all())], 200
        # return [item.json() for item in ItemModel.query.all()] # for "pythonic" code, we use list comprehensions and for performance benefits
        # return list(map(lambda x: x.json(), ItemModel.query.all())) # for "non-pythonic" code.
