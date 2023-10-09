from flask import Blueprint
from flask_restx import Api

authorizations = {
    "apikey": {"type": "apiKey", "in": "header", "name": "Authorization"},
    "password": {"type": "basic"},
}


bp = Blueprint("api", __name__)
api = Api(bp, authorizations=authorizations, security="apikey")

from netwerker.api.user.routes import ns

api.add_namespace(ns)
