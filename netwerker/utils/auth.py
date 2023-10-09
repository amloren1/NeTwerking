import datetime
from base64 import b64decode
from functools import wraps
from venv import logger
from xmlrpc.client import Boolean, boolean

import jwt
from flask import current_app, g, request
from werkzeug.datastructures import Authorization
from werkzeug.exceptions import BadRequest, Unauthorized
from werkzeug.security import check_password_hash

from netwerker.app import mongo
from netwerker.utils.mongo_queries import get_user


class BasicAuth(object):
    """
    Basic Authentication for Flask routes.
    """

    def __init__(self, scheme=None, header=None):
        self.scheme = scheme
        self.header = header

    def login_required(self, f=None, user_types=[]):
        def login_required_internal(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                """
                Decorator for securing route with authentication requirements. Parameters
                allow for customization of the authorization requirements.

                Parameters
                ----------
                f : function
                    The function to decorate.
                context : str
                    The type of client accessing the API. 
                """

                auth = self.get_auth()

                if auth is None:
                    raise Unauthorized("Invalid credentials")

                user, org = self.authenticate(auth)

                if len(user_types) > 0:
                    if not any([ut in user_types for ut in user.get("user_types")]):
                        raise Unauthorized(
                            "User type does not have permission to access this resource"
                        )
                # remove passwordHash field from user object
                user.pop("passwordHash", None)
                user.pop("pubKey", None)
                g.flask_httpauth_user = user
                g.flask_httpauth_org = org
                return f(*args, **kwargs)

            return decorated

        if f:
            return login_required_internal(f)
        return login_required_internal

    def authenticate(self, auth: Authorization):
        """
        Authenticate the user. This method must be overridden in a subclass.
        """

        # lookup user in mongo database using the provided email
        user, org = get_user(email=auth.username)

        # check the password hash
        if not check_password_hash(user.get("passwordHash"), auth.password):
            raise Unauthorized("Invalid credentials")

        return user, org

    def get_auth(self):
        """This method is to authorize basic connections"""
        # this version of the Authorization header parser is more flexible
        # than Werkzeug's, as it also accepts other schemes besides "Basic"
        header = self.header or "Authorization"
        if header not in request.headers:
            return None
        value = request.headers[header].encode("utf-8")
        try:
            scheme, credentials = value.split(b" ", 1)
            username, password = b64decode(credentials).split(b":", 1)
        except (ValueError, TypeError):
            raise BadRequest("Invalid Authorization header")
        return Authorization(
            scheme,
            {
                "username": username.decode("utf-8"),
                "password": password.decode("utf-8"),
            },
        )


class TokenAuth(BasicAuth):
    """TokenAuth class extends the OdyBasicAuth class.
    It's primary function is to do token authentications."""

    def __init__(self, scheme="Bearer", header=None):
        # super().__init__(scheme, header)
        super(TokenAuth, self).__init__(scheme, header)
        self.verify_token_callback = None

    def get_auth(self):
        """This method is to authorize tokens"""
        auth = None
        if self.header is None or self.header == "Authorization":
            auth_header = request.headers.get("Authorization")
            if auth_header:
                # Flask/Werkzeug do not recognize any authentication types
                # other than Basic or Digest, so here we parse the header by
                # hand
                try:
                    auth_type, token = auth_header.split(None, 1)
                    # Here we create an instance of the Authorization class
                    auth = Authorization(auth_type, {"token": token})
                except (ValueError, KeyError):
                    # The Authorization header is either empty or has no token
                    pass
        elif self.header in request.headers:
            # using a custom header, so the entire value of the header is
            # assumed to be a token
            token = request.headers.get(self.header)
            auth = Authorization(self.scheme, {"token": token})
        if auth and auth.type.lower() != self.scheme.lower():
            auth = None

        return auth

    def authenticate(self, auth: Authorization):
        """
        Authenticate the user. This method must be overridden in a subclass.
        """

        if False: # placeholder for future token validation
            raise Unauthorized("Invalid credentials")
        else:
            try:
                token = jwt.decode(
                    auth.get("token"),
                    current_app.config["SECRET_KEY"],
                    algorithms=["HS256"],
                )
            except jwt.ExpiredSignatureError:
                raise Unauthorized("Token expired")
            except jwt.InvalidTokenError:
                raise Unauthorized("Invalid token")

            user, org = get_user(token.get("uuid"))

        return user, org

    @staticmethod
    def generate_token(user, org, ttype="access"):
        """Generate a token for the user"""

        token = jwt.encode(
            {
                "uuid": user.get("uuid"),
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                "ttype": ttype,
                "org": org,
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return token


basic_auth = BasicAuth()
token_auth = TokenAuth()
