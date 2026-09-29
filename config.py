"""
Configurações gerais de segurança da API.

Centraliza tudo que antes estava espalhado no topo do main.py:
chave JWT, algoritmo, tempo de expiração do token, chave/objeto de
criptografia Fernet e o contexto de hashing de senhas (bcrypt).
"""

import os
from pathlib import Path

from passlib.context import CryptContext
from cryptography.fernet import Fernet

# Configurações do Token JWT
SECRET_KEY = "chave-secreta-do-projeto-ia-anonima-mude-em-producao"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuração da Criptografia Simétrica Fernet (AES-128 em modo CBC com HMAC)
# IMPORTANTE: a chave precisa ser sempre a mesma entre reinícios do servidor,
# senão todo dado criptografado anteriormente fica ilegível para sempre.
# Por isso ela é lida da variável de ambiente FERNET_KEY (recomendado em
# produção) e, se não existir, é gerada uma única vez e persistida em um
# arquivo local (fernet.key) para ser reaproveitada nas próximas execuções.
_FERNET_KEY_FILE = Path(__file__).resolve().parent / "fernet.key"


def _carregar_ou_criar_fernet_key() -> bytes:
    env_key = os.getenv("FERNET_KEY")
    if env_key:
        return env_key.encode()

    if _FERNET_KEY_FILE.exists():
        return _FERNET_KEY_FILE.read_bytes()

    nova_chave = Fernet.generate_key()
    _FERNET_KEY_FILE.write_bytes(nova_chave)
    return nova_chave


FERNET_KEY = _carregar_ou_criar_fernet_key()
cipher_suite = Fernet(FERNET_KEY)

# Configuração do Hashing de Senhas com Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
