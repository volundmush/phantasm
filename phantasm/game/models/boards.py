from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator

from mudpy.utils import lazy_property
from phantasm.game.locks.lockhandler import BaseLockHandler

from .mixins import HasLocks


class Board(Model, HasLocks):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    faction = fields.ForeignKeyField("factions.Faction", null=True, related_name="boards", on_delete=fields.RESTRICT)
    order = fields.SmallIntField(default=0)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)
    deleted_at = fields.DatetimeField(null=True)
    anonymous_name = fields.CharField(max_length=255, null=True)

    class Meta:
        ordering = ["faction", "order"]
        unique_together = ["faction", "order"]

    @lazy_property
    def locks(self) -> BaseLockHandler:
        return BaseLockHandler(self)

    def board_id(self) -> str:
        if self.faction:
            return f"{self.faction.abbreviation}{self.order}"
        return str(self.order)

    async def access(self, accessor: "ActingAs", access_type: str) -> bool:
        match access_type:
            case "read" | "post":
                if await self.locks.access(accessor, "admin"):
                    return True
                return await self.locks.access(accessor, access_type)
            case _:
                return await self.locks.access(accessor, access_type)

    class PydanticMeta:
        computed = ["board_id"]
        exclude = ["id"]

Board_Pydantic = pydantic_model_creator(Board, name="Board")
Board_Pydantic_List = pydantic_queryset_creator(Board)

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

    def post_id(self) -> str:
        if self.sub_order:
            return f"{self.order}.{self.sub_order}"
        return str(self.order)

    class Meta:
        ordering = ["board", "order", "sub_order"]
        unique_together = ["board", "order", "sub_order"]

    class PydanticMeta:
        computed = ["post_id"]
        exclude = ["id", "order", "sub_order"]

Post_Pydantic = pydantic_model_creator(Post, name="Post")
Post_Pydantic_List = pydantic_queryset_creator(Post)

class LastRead(Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("auth.User", related_name="board_read", on_delete=fields.CASCADE)
    post = fields.ForeignKeyField("boards.Post", related_name="user_read", on_delete=fields.CASCADE)
    read_at = fields.DatetimeField(auto_now_add=True, editable=True)
