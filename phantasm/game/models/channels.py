from tortoise.models import Model
from tortoise import fields


class Channel(Model):
    id = fields.IntField(primary_key=True)
    channel_category = fields.CharField(max_length=255, default='Uncategorized')
    name = fields.CharField(max_length=255, unique=True)
    description = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        unique_together = ["channel_category", "name"]
        ordering = ["channel_category", "name"]


class Message(Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("auth.User", related_name="channel_messages", on_delete=fields.RESTRICT)
    channel = fields.ForeignKeyField("channels.Channel", related_name="messages", on_delete=fields.RESTRICT)
    body = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        ordering = ["channel", "created_at"]
