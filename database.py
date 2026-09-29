from contextlib import asynccontextmanager

from fastapi import FastAPI
from prisma import Prisma

db = Prisma()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executado quando a API sobe: abre a conexão com o banco
    await db.connect()
    yield
    # Executado quando a API é encerrada: fecha a conexão
    await db.disconnect()
