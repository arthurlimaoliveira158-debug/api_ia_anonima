"""Rotas de auditoria (histórico de logs) e do módulo SIEM com IA."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ai_detector import DetetorAnomalias
from database import db
from schemas import LogResponse
from security import get_usuario_atual, registrar_log

router = APIRouter()

detector_ia = DetetorAnomalias()


@router.get("/logs", response_model=List[LogResponse], tags=["Auditoria"])
async def consultar_logs_auditoria(current_user=Depends(get_usuario_atual)):
    """Módulo de Auditoria: consulta o histórico cronológico de acessos e eventos do sistema."""
    await registrar_log(f"AUDITORIA: Consulta ao log geral de eventos executada por -> '{current_user.username}'")
    logs = await db.logauditoria.find_many(order={"dataHora": "desc"}, take=50)
    return [LogResponse(id=log.id, acao=log.acao, data_hora=log.dataHora) for log in logs]


@router.get("/siem/analise", tags=["Segurança IA"])
async def rodar_analise_ia(current_user=Depends(get_usuario_atual)):
    """Módulo SIEM IA: Varre os logs em busca de padrões de infiltração."""

    # Opcional: Garanta que apenas administradores acessem isso
    if current_user.username != "admin_master":
        raise HTTPException(status_code=403, detail="Acesso restrito ao SIEM.")

    resultado = await detector_ia.analisar_logs(db)
    await registrar_log(f"SIEM: Análise de IA executada por -> '{current_user.username}'")
    return resultado
