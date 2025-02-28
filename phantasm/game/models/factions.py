from tortoise.models import Model
from tortoise import fields


class Faction(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True)
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)
    description = fields.TextField()
    abbreviation = fields.CharField(max_length=10, unique=True)
    category = fields.CharField(max_length=255, default='Uncategorized')
    private = fields.BooleanField(default=True)
    hidden = fields.BooleanField(default=True)
    can_leave = fields.BooleanField(default=True)
    kick = fields.SmallIntField(default=2)
    start_rank = fields.SmallIntField(default=0)
    title_self = fields.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]


class Rank(Model):
    id = fields.IntField(primary_key=True)
    faction = fields.ForeignKeyField("factions.Faction", related_name="ranks", on_delete=fields.CASCADE)
    value = fields.SmallIntField()
    name = fields.CharField(max_length=255)
    permissions = fields.TextField(default='')

    class Meta:
        unique_together = ["faction", "value"]
        ordering = ["faction", "value"]


class Member(Model):
    id = fields.IntField(primary_key=True)
    faction = fields.ForeignKeyField("factions.Faction", related_name="members", on_delete=fields.CASCADE)
    character = fields.ForeignKeyField("characters.Character", related_name="factions", on_delete=fields.CASCADE)
    rank = fields.ForeignKeyField("factions.Rank", related_name="holders", on_delete=fields.RESTRICT)
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)
    permissions = fields.TextField(default='')
    title = fields.CharField(max_length=255, null=True)

    class Meta:
        unique_together = ["faction", "character"]
        ordering = ["faction", "character"]