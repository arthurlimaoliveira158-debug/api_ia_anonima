from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from config import SECRET_KEY, ALGORITHM
from database import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def registrar_log(acao: str):
    """Módulo de Auditoria: salva um evento com carimbo de data/hora via Prisma."""
    await db.logauditoria.create(data={"acao": acao})


async def get_usuario_atual(token: str = Depends(oauth2_scheme)):
    """Verifica e decodifica o Token JWT para autorizar rotas protegidas."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais de autenticação inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.usuario.find_unique(where={"username": username})
    if user is None:
        raise credentials_exception
    return user
