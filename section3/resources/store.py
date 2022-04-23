from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models.store import StoreModel
from schemas.store import StoreSchema

NAME_ALREADY_EXISTS = "A store with name '{}' already exists."
STORE_NOT_FOUND = "Store not found."
ERROR_INSERTING = "An error occured when inserting a store."

store_schema = StoreSchema()
store_list_schema = StoreSchema(many=True)


class Store(Resource):
    @classmethod
    def get(cls, name: str):
        store = StoreModel.find_by_name(name)
        if store:
            return store_schema.dump(store)
        return {"message": STORE_NOT_FOUND}, 404

    @classmethod
    @jwt_required()
    def post(cls, name: str):
        if StoreModel.find_by_name(name):
            return {"message": NAME_ALREADY_EXISTS.format(name)}, 400

        store = StoreModel(name=name)
        try:
            store.save_to_db()
        except:
            return {"message": ERROR_INSERTING}, 500
        return True, 201

    @classmethod
    @jwt_required()
    def delete(cls, name: str):
        store = StoreModel.find_by_name(name)
        if store:
            store.delete_from_db()

        return True


class StoreList(Resource):
    @classmethod
    def get(cls):
        return [store_list_schema.dump(StoreModel.find_all())]
