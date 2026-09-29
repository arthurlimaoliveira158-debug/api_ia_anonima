"""Esquemas Pydantic usados para validar entradas e formatar saídas da API."""

from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class DadoCreate(BaseModel):
    informacao: str


class DadoResponse(BaseModel):
    id: int
    informacao: str


class Token(BaseModel):
    access_token: str
    token_type: str


class LogResponse(BaseModel):
    id: int
    acao: str
    data_hora: datetime
