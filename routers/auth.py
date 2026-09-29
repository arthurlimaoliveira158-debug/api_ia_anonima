"""Rotas de autenticação: cadastro de usuários e login (JWT)."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, pwd_context
from database import db
from schemas import UserCreate, Token
from security import registrar_log

router = APIRouter(tags=["Autenticação"])


@router.post("/registrar", status_code=status.HTTP_201_CREATED)
async def registrar_usuario(user: UserCreate):
    """Módulo de Autenticação: cadastra novos usuários convertendo a senha diretamente em hash bcrypt."""
    db_user = await db.usuario.find_unique(where={"username": user.username})
    if db_user:
        raise HTTPException(status_code=400, detail="Este nome de usuário já está em uso.")

    # Gera o hash da senha via bcrypt com sal criptográfico
    hashed_password = pwd_context.hash(user.password)

    await db.usuario.create(data={"username": user.username, "passwordHash": hashed_password})

    await registrar_log(f"CADASTRO: Novo usuário registrado com sucesso -> '{user.username}'")
    return {"mensagem": "Usuário cadastrado com sucesso!"}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Módulo de Monitoramento e Autenticação: verifica credenciais e bloqueia após falhas consecutivas."""
    username = form_data.username
    password = form_data.password

    # 1. Checa se o usuário está bloqueado pelo monitoramento de tentativas mal-sucedidas
    tentativa_registro = await db.tentativalogin.find_first(where={"username": username})
    if tentativa_registro and tentativa_registro.bloqueadoAte:
        if datetime.now(timezone.utc) < tentativa_registro.bloqueadoAte:
            await registrar_log(f"BLOQUEIO: Tentativa de login rejeitada para conta suspensa -> '{username}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conta temporariamente bloqueada por excesso de tentativas falhas. Tente novamente em 15 minutos."
            )
        else:
            # O tempo de bloqueio expirou, limpa o registro
            await db.tentativalogin.update(
                where={"id": tentativa_registro.id},
                data={"tentativas": 0, "bloqueadoAte": None},
            )
            tentativa_registro = None

    # 2. Busca o usuário no banco de dados e valida a senha
    user = await db.usuario.find_unique(where={"username": username})
    if not user or not pwd_context.verify(password, user.passwordHash):
        # Aumenta o contador de tentativas incorretas
        if not tentativa_registro:
            await db.tentativalogin.create(data={"username": username, "tentativas": 1})
        else:
            novas_tentativas = tentativa_registro.tentativas + 1
            dados_atualizacao = {"tentativas": novas_tentativas}
            # Se atingir 3 falhas, bloqueia a conta por 15 minutos (mitigação contra força bruta)
            if novas_tentativas >= 3:
                dados_atualizacao["bloqueadoAte"] = datetime.now(timezone.utc) + timedelta(minutes=15)
            await db.tentativalogin.update(where={"id": tentativa_registro.id}, data=dados_atualizacao)

        await registrar_log(f"FALHA DE LOGIN: Credenciais incorretas para -> '{username}'")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha incorretos.")

    # 3. Se o login foi bem-sucedido, reseta os erros
    if tentativa_registro:
        await db.tentativalogin.delete(where={"id": tentativa_registro.id})

    # 4. Gera o Token de Sessão (JWT)
    tempo_expiracao = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_jwt = jwt.encode({"sub": user.username, "exp": tempo_expiracao}, SECRET_KEY, algorithm=ALGORITHM)

    await registrar_log(f"LOGIN: Acesso concedido e token gerado para -> '{user.username}'")
    return {"access_token": token_jwt, "token_type": "bearer"}
