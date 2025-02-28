from tortoise.models import Model
from tortoise import fields


class Channel(Model):
    id = fields.IntField(primary_key=True)
    channel_type = fields.SmallIntField(default=0)
    name = fields.CharField(max_length=255)
    description = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        unique_together = ["channel_type", "name"]
        ordering = ["channel_type", "name"]


class Member(Model):
    id = fields.IntField(primary_key=True)
    channel = fields.ForeignKeyField("channels.Channel", related_name="speakers", on_delete=fields.RESTRICT)
    user = fields.ForeignKeyField("auth.User", related_name="channels", on_delete=fields.RESTRICT)
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)

    class Meta:
        unique_together = ["channel", "user"]
        index_together = ["user", "channel"]
        ordering = ["channel", "user"]


class Message(Model):
    id = fields.BigIntField(primary_key=True)
    member = fields.ForeignKeyField("channels.Member", related_name="messages", on_delete=fields.RESTRICT)
    body = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)

    class Meta:
        ordering = ["channel", "created_at"]