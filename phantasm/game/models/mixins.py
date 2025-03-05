import typing
from tortoise import fields

class TimestampMixin:
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)


class HasLocks:
    lock_data = fields.JSONField(null=True)

    async def save_lock(self, access_type: str, lock_str: str):
        if not self.lock_data:
            self.lock_data = {}
        self.lock_data[access_type] = lock_str
        await self.save()

    async def load_lock(self, access_type: str) -> typing.Optional[str]:
        if not self.lock_data:
            return None
        return self.lock_data.get(access_type, None)

    async def clear_lock(self, access_type: str):
        if not self.lock_data:
            return
        if access_type in self.lock_data:
            del self.lock_data[access_type]
            await self.save()

    async def clear_all_locks(self):
        self.lock_data = {}
        await self.save()

    async def access(self, accessor: "ActingAs", access_type: str, default: typing.Optional[str] = None) -> bool:
        return await self.locks.access(accessor, access_type, default=default)