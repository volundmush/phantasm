from tortoise.models import Model
from tortoise import fields

from .mixins import TimestampMixin

class Info(TimestampMixin, Model):
    id = fields.IntField(primary_key=True)
    # 0 is user, 1 is character, 2+ are reserved for game-specific purposes.
    entity_type = fields.SmallIntField(default=0)
    entity_id = fields.IntField()
    category_id = fields.SmallIntField(default=0)
    name = fields.CharField(max_length=255)
    body = fields.TextField()
    locked = fields.BooleanField(default=False)
    private = fields.BooleanField(default=False)

    class Meta:
        unique_together = ["entity_type", "entity_id", "category_id", "name"]
        ordering = ["entity_type", "entity_id", "category_id", "name"]