from collections import deque
from uuid import uuid4

import jwt
from bson import ObjectId
from flask import current_app, g, request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from werkzeug.exceptions import BadRequest, Forbidden
from werkzeug.security import generate_password_hash

from netwerker.api import user
from netwerker.api.user.schemas import *
from netwerker.app import mongo
from netwerker.utils.auth import basic_auth, token_auth
from netwerker.utils.misc import bfs_friendship_distance, generate_friendship_hash
from netwerker.utils.mongo_queries import get_user

ns = Namespace("users", description="Operations related to clients")


@ns.route("/login")
class Login(Resource):
    @ns.doc(security="password")
    @basic_auth.login_required()
    def post(self):
        # get the credentials from the request
        # validate the credentials
        user = g.flask_httpauth_user
        org = g.flask_httpauth_org

        # generate a token
        token = token_auth.generate_token(user, org)

        return {"user": user, "token": token}, 201


# @ns.route("/token-validation")
# class TokenValidation(Resource):
#     def get(self):
#         """validate token"""
#         token = request.headers.get("Authorization")
#         if not token:
#             raise BadRequest("No token provided")

#         token = token.split(" ")[1]
#         try:
#             decoded_token = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
#             user = mongo.db.users.find_one({"uuid": decoded_token.get("uuid")}, {"_id": False})
#             if not user:
#                 raise BadRequest("Invalid token")
#         except Exception as e:
#             # log the error
#             logger = current_app.logger
#             logger.error(e)

#             raise BadRequest("Invalid token")

#         return


@ns.route("/all")
class Users(Resource):
    """
    Bring up details on all users in system
    """

    # @token_auth.login_required(user_types=("admin",))
    # @responds(schema=AllUsersSchema, api=ns, status_code=200)
    def get(self):
        # user, org = g.flask_httpauth_user, g.flask_httpauth_org

        users_cursor = mongo.db.users.find(
            {}, {"friends": 0, "passwordHash": 0, "_id": 0}
        )
        # Convert the cursor into a list
        users = list(users_cursor)

        payload = {"items": users, "total_items": len(users)}

        return payload


@ns.route("")
class NewUser(Resource):
    """
    Create new user. Update and view current user details.
    """

    # @token_auth.login_required(user_types=("admin",))
    @accepts(schema=UserSchema, api=ns)
    @responds(schema=UserSchema, api=ns, status_code=201)
    def post(self):
        # ensure user does not already exist by email address
        data = request.parsed_obj
        user = get_user(email=data.get("email").lower(), none_on_fail=True)

        if user:
            raise BadRequest("user already exists")

        # hash the password
        pword_hash = generate_password_hash(data.get("password"))

        # remove password from data, add password hash
        del data["password"]
        data["passwordHash"] = pword_hash

        data["uuid"] = str(uuid4())
        data["email"] = data["email"].lower()
        data[
            "email_verified"
        ] = True  # TODO: set to False and send email to user to verify email address

        user = mongo.db.users.insert_one(data)

        return data


@ns.route("/<string:uuid>")
class User(Resource):
    """access a single user"""

    # @token_auth.login_required()
    @accepts(schema=UserPatchSchema, api=ns)
    @responds(api=ns, status_code=200)
    def patch(self, uuid):
        data = request.parsed_obj
        mongo.db.users.update_one({"uuid": uuid}, {"$set": data})

        return

    @responds(schema=UserSchema(), api=ns, status_code=200)
    def get(self, uuid):
        user = get_user(uuid=uuid)
        return user


@ns.route("/<string:uuid>/friends")
class UserFriends(Resource):
    """access a single user's friends"""

    @responds(schema=AllUsersSchema, api=ns, status_code=200)
    def get(self, uuid):
        user = get_user(uuid=uuid, get_friends=True)
        # iterate through friends and get their details
        for i, friend_id in enumerate(user.get("friends", [])):
            friend = get_user(_id=friend_id)
            user["friends"][i] = friend

        return {
            "items": user.get("friends", []),
            "total_items": len(user.get("friends", [])),
        }

    @ns.param("friend_uuid", "new friend uuid")
    @responds(api=ns, status_code=201)
    def post(self, uuid):
        friend_uuid = request.args.get("friend_uuid")
        if not friend_uuid:
            raise BadRequest("Missing friend uuid")

        current_user = get_user(uuid=uuid)
        friend = get_user(uuid=friend_uuid)
        if not friend:
            raise BadRequest("Invalid friend uuid")
        # Generate the hash (replace this with your actual hash generation logic)
        friendship_hash = generate_friendship_hash(
            str(current_user["_id"]), str(friend["_id"])
        )

        # check if users are already friends
        cursor = mongo.db.friends.find_one({"friendship_hash": friendship_hash})
        if cursor:
            raise BadRequest("Users are already friends")

        # sort the two _ids to ensure the hash is the same regardless of the order
        sorted_ids = sorted([current_user["_id"], friend["_id"]])

        # Add friend to user's friend list along with hash
        mongo.db.users.update_one(
            {"_id": current_user["_id"]}, {"$push": {"friends": friend["_id"]}}
        )

        # Add user to friend's friend list along with hash
        mongo.db.users.update_one(
            {"_id": friend["_id"]}, {"$push": {"friends": current_user["_id"]}}
        )

        # Add the friendship hash to the friends
        mongo.db.friends.insert_one(
            {
                "friendship_hash": friendship_hash,
                "user1_id": sorted_ids[0],
                "user2": sorted_ids[1],
            }
        )

    # TODO: configure mongo as a replica set so transactions can be used
    # with mongo.db.client.start_session() as session:
    #     try:
    #         with session.start_transaction():
    #             # Add friend to user's friend list along with hash
    #             mongo.db.users.update_one({"_id": current_user["_id"]}, {"$push": {"friends": friend["_id"]}}, session=session)

    #             # Add user to friend's friend list along with hash
    #             mongo.db.users.update_one({"_id": friend["_id"]}, {"$push": {"friends": current_user["_id"]}}, session=session)

    #              # Commit the transaction
    #             session.commit_transaction()

    #         return {"message": "Friend added successfully"}
    #     except Exception as e:
    #         # Abort the transaction in case of error
    #         session.abort_transaction()
    #         raise e


@ns.route("/<string:user_uuid>/friends/distance/<string:friend_uuid>")
class UserDistance(Resource):
    """get distance between two users"""

    # @responds(api=ns, status_code=200)
    def get(self, user_uuid, friend_uuid):
        user = get_user(uuid=user_uuid)
        friend = get_user(uuid=friend_uuid)

        # find the distance between the two users
        distance = bfs_friendship_distance(
            start_user_id=str(user["_id"]), target_user_id=str(friend["_id"])
        )

        return {"distance": distance}
