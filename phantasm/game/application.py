import mudpy
import importlib
from pathlib import Path
from fastapi import FastAPI
from hypercorn import Config
from hypercorn.asyncio import serve
from tortoise import Tortoise
from mudpy.game.application import Application as OldApplication


class Application(OldApplication):

    def __init__(self):
        super().__init__()
        self.fastapi_config = None
        self.fastapi_instance = None

    async def setup_tortoise(self):
        settings = mudpy.SETTINGS["GAME"]["tortoise"]
        await Tortoise.init(**settings)
        await Tortoise.generate_schemas()

    async def setup_fastapi(self):
        settings = mudpy.SETTINGS
        shared = settings["SHARED"]
        tls = settings["TLS"]
        networking = settings["GAME"]["networking"]
        self.fastapi_config = Config()
        self.fastapi_config.title = shared["name"]

        external = shared["external"]
        bind_to = f"{external}:{networking['port']}"
        self.fastapi_config.bind = [bind_to]

        if Path(tls["certificate"]).exists():
            self.fastapi_config.certfile = tls["cert"]
        if Path(tls["key"]).exists():
            self.fastapi_config.keyfile = tls["key"]

        self.fastapi_instance = FastAPI()
        routers = settings["FASTAPI"]["routers"]
        for k, v in routers.items():
            v = importlib.import_module(v)
            self.fastapi_instance.include_router(v.router, prefix=f"/{k}", tags=[k])

    async def setup(self):
        await super().setup()
        await self.setup_tortoise()
        await self.setup_fastapi()

    async def start(self):
        await serve(self.fastapi_instance, self.fastapi_config)