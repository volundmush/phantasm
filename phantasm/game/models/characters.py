from tortoise.models import Model
from tortoise import fields

class Character(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("auth.User", related_name="characters", on_delete=fields.RESTRICT)
    name = fields.CharField(max_length=255, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)