from fastapi import FastAPI
from pydantic import BaseModel

from database import lifespan
from routers import auth, dados, auditoria

app = FastAPI(
    title="API IA Anônima - Controle de Acesso e Proteção de Dados",
    description="API com autenticação Bcrypt/JWT, criptografia simétrica Fernet, auditoria de logs e ORM Prisma.",
    version="2.0.0",
    lifespan=lifespan,
)

# No main.py
from pydantic import BaseModel

class PanicoResponse(BaseModel):
    mensagem: str

@app.post("/panico", response_model=PanicoResponse, tags=["Segurança de Usuário"])
async def acionar_botao_panico(current_user=Depends(get_usuario_atual)):
    """Acionado pelo usuário quando ele percebe algo estranho na sua conta."""
    
    # 1. Trava a conta para proteger os dados
    await db.usuario.update(
        where={"id": current_user.id},
        data={"contaSuspensa": True, "emAlerta": True}
    )
    
    # 2. Registra o evento de pânico
    await db.alertapanico.create(data={"usuarioId": current_user.id})
    
    # 3. Registra na auditoria (a IA vai ler isso!)
    await registrar_log(f"PANICO_USUARIO: Conta '{current_user.username}' acionou alerta de segurança.")
    
    return {"mensagem": "Conta protegida imediatamente. A IA está analisando o tráfego recente."}

app.include_router(auth.router)
app.include_router(dados.router)
app.include_router(auditoria.router)
