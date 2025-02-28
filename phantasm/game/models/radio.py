from tortoise.models import Model
from tortoise import fields

class Frequency(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True)
    description = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)
    owner = fields.ForeignKeyField("characters.Character", related_name="owned_frequencies", on_delete=fields.RESTRICT)
    admin = fields.ManyToManyField("characters.Character", related_name="admin_of_frequencies")
    moderators = fields.ManyToManyField("characters.Character", related_name="moderator_of_frequencies")


class Message(Model):
    id = fields.BigIntField(primary_key=True)
    character = fields.ForeignKeyField("characters.Character", related_name="channel_messages", on_delete=fields.RESTRICT)
    alternate_name = fields.CharField(max_length=255, null=True)
    frequency = fields.ForeignKeyField("radio.Frequency", related_name="messages", on_delete=fields.RESTRICT)
    body = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        ordering = ["frequency", "created_at"]
