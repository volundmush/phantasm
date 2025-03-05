import mudpy
import phantasm
import importlib
import asyncpg
from lark import Lark
from pathlib import Path
from fastapi import FastAPI
from hypercorn import Config
from hypercorn.asyncio import serve
from mudpy.game.application import Application as OldApplication
from mudpy.utils import callables_from_module

class Application(OldApplication):

    def __init__(self):
        super().__init__()
        self.fastapi_config = None
        self.fastapi_instance = None

    async def setup_asyncpg(self):
        settings = mudpy.SETTINGS["GAME"]["postgresql"]
        pool = await asyncpg.create_pool(**settings)
        phantasm.PGPOOL = pool

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

    async def setup_lark(self):
        absolute_phantasm = Path(phantasm.__file__).parent
        grammar = absolute_phantasm / "grammar.lark"
        with open(grammar, "r") as f:
            data = f.read()
            parser = Lark(data)
            phantasm.LOCKPARSER = parser

    async def setup(self):
        await super().setup()
        await self.setup_lark()
        await self.setuo_asyncpg()
        await self.setup_fastapi()

        for k, v in mudpy.SETTINGS["GAME"].get("lockfuncs", dict()).items():
            lock_funcs = callables_from_module(v)
            for name, func in lock_funcs.items():
                phantasm.LOCKFUNCS[name] = func


    async def start(self):
        await serve(self.fastapi_instance, self.fastapi_config)