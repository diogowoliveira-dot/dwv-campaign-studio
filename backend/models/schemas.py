from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Auth
class LoginRequest(BaseModel):
    email: str
    senha: str


class LoginResponse(BaseModel):
    user: dict
    token: str


# Executivos
class ExecutivoInput(BaseModel):
    nome: str
    cargo: str = "Executivo de Parcerias"
    regiao: str = ""
    whatsapp: str = ""
    email: str = ""


class ExecutivoResponse(BaseModel):
    id: str
    nome: str
    cargo: str
    regiao: str
    whatsapp: str
    email: str
    foto_url: Optional[str] = None
    ativo: bool = True


# Campanhas
class CampanhaInput(BaseModel):
    tipo: str
    cliente: str
    empreendimento: str
    url_site: str = ""
    executivo_id: str
    copy_base: str
    data_evento: Optional[str] = None
    local_evento: Optional[str] = None


class CampanhaResponse(BaseModel):
    id: str
    tipo: str
    cliente: str
    empreendimento: str
    status: str
    criada_em: str


class PecaResponse(BaseModel):
    id: str
    formato: str
    versao: int
    html: str
    arquivo_url: str


class PecaResumo(BaseModel):
    id: str
    formato: str
    versao: int
    arquivo_url: str
    has_html: bool = True


class MensagemResponse(BaseModel):
    id: str
    role: str
    conteudo: str
    criada_em: str


class CampanhaCompleta(CampanhaResponse):
    briefing: dict
    pecas: list[PecaResumo]
    mensagens: list[MensagemResponse]
    executivo: ExecutivoResponse


class EditarRequest(BaseModel):
    mensagem: str
    formato: str


class EditarResponse(BaseModel):
    peca: PecaResponse
    mensagem_assistente: str
