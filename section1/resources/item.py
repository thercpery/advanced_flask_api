from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required
from models.item import ItemModel

BLANK_ERROR = "'{}' cannot be blank."
NAME_ALREADY_EXISTS = "An item with name '{}' already exists."
ERROR_INSERTING = "An error occured while inserting the item."
ERROR_RETRIEVING = "An error occured while retrieving the item."
ITEM_NOT_FOUND = "Item not found."
ITEM_DELETED = "Item deleted."


class Item(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument(
        "price",
        type=float,  # turns to float
        required=True,  # is required
        help=BLANK_ERROR.format("price"),
    )
    parser.add_argument(
        "store_id",
        type=int,  # turns to float
        required=True,  # is required
        help=BLANK_ERROR.format("store_id"),
    )

    """ Using instance methods. """
    # item = Item()
    # item.get()

    """ Using class methods """
    # Item.get()

    @classmethod
    @jwt_required()  # analogy: In Javascript terms, this is the "auth.verify"
    def get(cls, name: str):
        try:
            item = ItemModel.find_by_name(name)
            if item:
                # If item is found
                return item.json()
        except:
            return {"message": ERROR_RETRIEVING}, 500
        # If item not found
        return {"message": ITEM_NOT_FOUND}, 404

    @classmethod
    @jwt_required()  # analogy: In Javascript terms, this is the "auth.verify"
    def post(cls, name: str):
        if ItemModel.find_by_name(name):
            # If item already exists return false
            return {"message": NAME_ALREADY_EXISTS.format(name)}, 400

        data = Item.parser.parse_args()
        item = ItemModel(name, **data)

        try:
            item.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, 500

        return True, 201

    @classmethod
    @jwt_required()  # analogy: In Javascript terms, this is the "auth.verify"
    def delete(cls, name: str):
        item = ItemModel.find_by_name(name)

        if item:
            item.delete_from_db()
            return {"message": ITEM_DELETED}, 201

        return {"message": ITEM_NOT_FOUND}, 404

    @classmethod
    @jwt_required(
        fresh=False
    )  # analogy: In Javascript terms, this is the "auth.verify"
    def put(cls, name: str):
        data = Item.parser.parse_args()

        item = ItemModel.find_by_name(name)

        if item is None:
            # If item does not exist create one.
            item = ItemModel(name, data["price"], data["store_id"])
        else:
            # If item exists update the existing item.
            item.price = data["price"]
            if data["store_id"]:
                item.store_id = data["store_id"]

        item.save_to_db()
        return True, 201


class ItemList(Resource):
    @classmethod
    def get(cls):
        return [item.json() for item in ItemModel.find_all()], 200
        # return [item.json() for item in ItemModel.query.all()] # for "pythonic" code, we use list comprehensions and for performance benefits
        # return list(map(lambda x: x.json(), ItemModel.query.all())) # for "non-pythonic" code.
