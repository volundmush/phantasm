from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator

from .mixins import TimestampMixin

class User(TimestampMixin, Model):
    id = fields.UUIDField(primary_key=True)
    # always save to email field as lowercase.
    email = fields.CharField(max_length=255, unique=True)
    admin_level = fields.SmallIntField(default=0)
    # Uniqueness of username will be handled by the application.
    display_name = fields.CharField(max_length=255, null=True, default=None)
    characters = fields.ReverseRelation["characters.Character"]

User_Pydantic = pydantic_model_creator(User, name="User")
User_Pydantic_List = pydantic_queryset_creator(User)

class Passwords(TimestampMixin, Model):
    id = fields.IntField(primary_key=True)
    user = fields.ForeignKeyField("auth.User", related_name="passwords", on_delete=fields.CASCADE)
    created_at = fields.DatetimeField(null=False, auto_now_add=True)
    password = fields.TextField()

    class Meta:
        ordering = ["-created_at"]
        index_together = ["user", "created_at"]



class LoginRecord(Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("auth.User", related_name="login_records", on_delete=fields.CASCADE)
    created_at = fields.DatetimeField(null=False, auto_now_add=True)
    ip_address = fields.CharField(max_length=255, index=True)
    user_agent = fields.TextField(null=True, default=None)
    success = fields.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        index_together = ["user", "created_at"]