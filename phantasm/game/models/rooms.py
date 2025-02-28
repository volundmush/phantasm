from tortoise.models import Model
from tortoise import fields


class Region(Model):
    id = fields.IntField(primary_key=True)
    parent = fields.ForeignKeyField("rooms.Region", related_name="children", on_delete=fields.RESTRICT)
    name = fields.CharField(max_length=255)

class Room(Model):
    id = fields.IntField(primary_key=True)
    region = fields.ForeignKeyField("rooms.Region", related_name="rooms", on_delete=fields.RESTRICT)
    name = fields.CharField(max_length=255)

class Event(Model):
    id = fields.BigIntField(primary_key=True)
    room = fields.ForeignKeyField("rooms.Room", related_name="events", on_delete=fields.RESTRICT)
    character = fields.ForeignKeyField("characters.Character", related_name="room_events", on_delete=fields.RESTRICT)
    as_name = fields.CharField(max_length=255)
    event_type = fields.SmallIntField(default=0)
    text = fields.TextField()
