from setuptools import find_packages, setup

__version__ = "0.1"

setup(
    name="netwerker",
    version=__version__,
    packages=find_packages(),
    install_requires=[
        "boto3",
        "idna",
        "flask",
        "flask-cors",
        "flask-restx",
        "flask-marshmallow",
        "python-dotenv",
        "passlib",
        "apispec[yaml]",
        "apispec-webframeworks",
        "Werkzeug",
        "marshmallow-sqlalchemy",
    ],
)
