from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator

class Character(Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("auth.User", related_name="characters", on_delete=fields.RESTRICT)
    name = fields.CharField(max_length=255, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

Character_Pydantic = pydantic_model_creator(Character, name="Character")
Character_Pydantic_List = pydantic_queryset_creator(Character)