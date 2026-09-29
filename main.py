from fastapi import FastAPI

from database import lifespan
from routers import auth, dados, auditoria

app = FastAPI(
    title="API IA Anônima - Controle de Acesso e Proteção de Dados",
    description="API com autenticação Bcrypt/JWT, criptografia simétrica Fernet, auditoria de logs e ORM Prisma.",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(dados.router)
app.include_router(auditoria.router)
