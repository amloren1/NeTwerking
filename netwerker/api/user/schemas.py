from marshmallow import Schema, fields, validate

from netwerker.app import ma


class UserSchema(Schema):
    # firstname = fields.String(required=True)
    # lastname = fields.String(required=True)
    # userTypes = fields.List(fields.String(), required=True)
    name = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(
        required=True, load_only=True, validate=validate.Length(min=3, max=50)
    )
    uuid = fields.UUID(dump_only=True)


class UserPatchSchema(Schema):
    # firstname = fields.String() # maybe don't allow this to be changed
    # lastname = fields.String()
    email = fields.Email()
    # password = fields.String(load_only=True, validate=validate.Length(min=3, max=50))
    uuid = fields.UUID(dump_only=True)


class AllUsersSchema(Schema):
    items = fields.Nested(UserSchema(many=True))
    total_items = fields.Integer()
