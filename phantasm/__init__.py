import asyncpg

LOCKPARSER = None
LOCKFUNCS = dict()
PGPOOL: asyncpg.Pool = None