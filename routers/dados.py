"""Rotas de dados pessoais criptografados com Fernet (AES-128)."""

from typing import List

from fastapi import APIRouter, Depends, status

from config import cipher_suite
from database import db
from schemas import DadoCreate, DadoResponse
from security import get_usuario_atual, registrar_log

router = APIRouter(tags=["Dados Criptografados"])


@router.post("/dados", status_code=status.HTTP_201_CREATED)
async def salvar_dado_pessoal(dado: DadoCreate, current_user=Depends(get_usuario_atual)):
    """Módulo de Criptografia: cifra o dado em Fernet (AES-128) antes de salvar via Prisma."""
    texto_cifrado = cipher_suite.encrypt(dado.informacao.encode()).decode()

    await db.dadopessoal.create(
        data={"usuarioId": current_user.id, "dadoCriptografado": texto_cifrado}
    )

    await registrar_log(f"INSERÇÃO DE DADO: Novo registro criptografado salvo por -> '{current_user.username}'")
    return {"mensagem": "Dado criptografado e armazenado com segurança!"}


@router.get("/dados", response_model=List[DadoResponse])
async def listar_dados_pessoais(current_user=Depends(get_usuario_atual)):
    """Módulo de Criptografia: busca no banco os dados ilegíveis e decifra para o titular legítimo."""
    dados_db = await db.dadopessoal.find_many(where={"usuarioId": current_user.id})

    dados_decifrados = []
    for registro in dados_db:
        try:
            # Decifra o texto armazenado no banco para visualização
            texto_limpo = cipher_suite.decrypt(registro.dadoCriptografado.encode()).decode()
            dados_decifrados.append(DadoResponse(id=registro.id, informacao=texto_limpo))
        except Exception:
            # Proteção caso a chave de criptografia tenha sido alterada ou corrompida
            dados_decifrados.append(
                DadoResponse(id=registro.id, informacao="[ERRO: Não foi possível decifrar o dado]")
            )

    await registrar_log(f"CONSULTA: Leitura e decifragem de dados executada por -> '{current_user.username}'")
    return dados_decifrados
