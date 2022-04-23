from flask_restful import Resource
from flask_jwt_extended import jwt_required
from models.store import StoreModel
from schemas.store import StoreSchema
from libs.strings import gettext

store_schema = StoreSchema()
store_list_schema = StoreSchema(many=True)


class Store(Resource):
    @classmethod
    def get(cls, name: str):
        store = StoreModel.find_by_name(name)
        if store:
            return store_schema.dump(store)
        return {"message": gettext("store_not_found")}, 404

    @classmethod
    @jwt_required()
    def post(cls, name: str):
        if StoreModel.find_by_name(name):
            return {"message": gettext("store_name_exists").format(name)}, 400

        store = StoreModel(name=name)
        try:
            store.save_to_db()
        except:
            return {"message": gettext("store_error_inserting")}, 500
        return True, 201

    @classmethod
    @jwt_required()
    def delete(cls, name: str):
        store = StoreModel.find_by_name(name)
        if store:
            store.delete_from_db()

        return {"message": gettext("store_deleted")}, 201


class StoreList(Resource):
    @classmethod
    def get(cls):
        return [store_list_schema.dump(StoreModel.find_all())]
