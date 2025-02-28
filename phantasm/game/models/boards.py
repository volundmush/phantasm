from tortoise.models import Model
from tortoise import fields

class Board(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    faction = fields.ForeignKeyField("factions.Faction", null=True, related_name="boards", on_delete=fields.RESTRICT)
    order = fields.SmallIntField(default=0)
    description = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)
    deleted_at = fields.DatetimeField(null=True)
    anonymous_name = fields.CharField(max_length=255, null=True)

    class Meta:
        ordering = ["faction", "order"]
        unique_together = ["faction", "order"]


class Post(Model):
    id = fields.IntField(primary_key=True)
    board = fields.ForeignKeyField("boards.Board", related_name="posts", on_delete=fields.CASCADE)
    order = fields.IntField(default=0)
    sub_order = fields.IntField(default=0)
    poster = fields.ForeignKeyField("characters.Character", related_name="posts", on_delete=fields.RESTRICT)
    alternate_name = fields.CharField(max_length=255, null=True)
    title = fields.CharField(max_length=255)
    body = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    def display_order(self) -> str:
        if self.sub_order > 0:
            return f"{self.order}.{self.sub_order}"
        return str(self.order)

    class Meta:
        ordering = ["board", "order", "sub_order"]
        unique_together = ["board", "order", "sub_order"]

class LastRead(Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("auth.User", related_name="board_read", on_delete=fields.CASCADE)
    post = fields.ForeignKeyField("boards.Post", related_name="user_read" on_delete=fields.CASCADE)
    read_at = fields.DateTimeField(auto_now_add=True, editable=True)
