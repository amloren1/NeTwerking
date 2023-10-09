import logging
import sys

from flask import Flask
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_pymongo import PyMongo

from netwerker.config import Config

conf = Config()

cors = CORS()
ma = Marshmallow()
mongo = PyMongo()

# Define the log format
log_format = (
    "%(asctime)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
)

# # Set up the root logger
# logging.basicConfig(
#     stream=sys.stdout,  # Log to stdout
#     level=conf.LOG_LEVEL,  # Use the log level from the configuration
#     format=log_format,  # Use the defined log format
# )

# Create a specific logger
logger = logging.getLogger("netwerker_log")

# Set up the logger
logger.setLevel(conf.LOG_LEVEL)  # Use the log level from the configuration
handler = logging.StreamHandler(sys.stdout)  # Log to stdout
handler.setFormatter(logging.Formatter(log_format))  # Use the defined log format
logger.addHandler(handler)


def create_app():
    app = Flask(__name__, static_folder="static")
    app.logger.addHandler(handler)
    app.config.from_object(conf)

    cors.init_app(app)
    ma.init_app(app)
    mongo.init_app(app)

    from netwerker.api import api, bp

    app.register_blueprint(bp)

    return app
