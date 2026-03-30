from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from models.schemas import (
    CampanhaInput, CampanhaResponse, CampanhaCompleta,
    EditarRequest, EditarResponse, PecaResponse, MensagemResponse,
)
from dependencies import get_current_user
from db import get_db
from services.generator import gerar_campanha_completa
from services.editor import editar_peca

router = APIRouter()


@router.get("", response_model=list[CampanhaResponse])
async def listar(user: dict = Depends(get_current_user)):
    db = get_db()
    res = (
        db.table("campanhas")
        .select("*")
        .eq("usuario_id", user["id"])
        .order("criada_em", desc=True)
        .execute()
    )
    return res.data


@router.post("", response_model=CampanhaResponse)
async def criar(data: CampanhaInput, user: dict = Depends(get_current_user)):
    db = get_db()
    row = {
        "id": str(uuid4()),
        "usuario_id": user["id"],
        "tipo": data.tipo,
        "cliente": data.cliente,
        "empreendimento": data.empreendimento,
        "executivo_id": data.executivo_id,
        "briefing": data.model_dump(),
        "status": "rascunho",
    }
    res = db.table("campanhas").insert(row).execute()
    return res.data[0]


@router.get("/{campanha_id}", response_model=CampanhaCompleta)
async def obter(campanha_id: str, user: dict = Depends(get_current_user)):
    db = get_db()

    campanha = (
        db.table("campanhas")
        .select("*")
        .eq("id", campanha_id)
        .eq("usuario_id", user["id"])
        .single()
        .execute()
    )
    if not campanha.data:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    executivo = db.table("executivos").select("*").eq("id", campanha.data["executivo_id"]).single().execute()
    pecas = db.table("pecas").select("*").eq("campanha_id", campanha_id).eq("is_atual", True).execute()
    mensagens = db.table("mensagens").select("*").eq("campanha_id", campanha_id).order("criada_em").execute()

    return {
        **campanha.data,
        "executivo": executivo.data,
        "pecas": pecas.data,
        "mensagens": mensagens.data,
    }


@router.post("/{campanha_id}/gerar")
async def gerar(campanha_id: str, user: dict = Depends(get_current_user)):
    db = get_db()

    campanha = (
        db.table("campanhas")
        .select("*")
        .eq("id", campanha_id)
        .eq("usuario_id", user["id"])
        .single()
        .execute()
    )
    if not campanha.data:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    executivo = db.table("executivos").select("*").eq("id", campanha.data["executivo_id"]).single().execute()
    if not executivo.data:
        raise HTTPException(status_code=404, detail="Executivo não encontrado")

    briefing = campanha.data["briefing"]

    try:
        resultado = await gerar_campanha_completa(briefing, executivo.data, db, campanha_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na geração: {str(e)}")

    db.table("campanhas").update({"status": "gerada"}).eq("id", campanha_id).execute()

    return resultado


@router.delete("/{campanha_id}")
async def deletar(campanha_id: str, user: dict = Depends(get_current_user)):
    db = get_db()

    campanha = (
        db.table("campanhas")
        .select("id")
        .eq("id", campanha_id)
        .eq("usuario_id", user["id"])
        .single()
        .execute()
    )
    if not campanha.data:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    # Delete related data first (SQLite doesn't cascade like Postgres always)
    db.table("mensagens").delete().eq("campanha_id", campanha_id).execute()
    db.table("pecas").delete().eq("campanha_id", campanha_id).execute()
    db.table("campanhas").delete().eq("id", campanha_id).execute()

    return {"ok": True}


@router.post("/{campanha_id}/editar", response_model=EditarResponse)
async def editar(campanha_id: str, req: EditarRequest, user: dict = Depends(get_current_user)):
    db = get_db()

    # Verify ownership
    campanha = (
        db.table("campanhas")
        .select("id")
        .eq("id", campanha_id)
        .eq("usuario_id", user["id"])
        .single()
        .execute()
    )
    if not campanha.data:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    # Buscar peca atual
    peca = (
        db.table("pecas")
        .select("*")
        .eq("campanha_id", campanha_id)
        .eq("formato", req.formato)
        .eq("is_atual", True)
        .single()
        .execute()
    )
    if not peca.data:
        raise HTTPException(status_code=404, detail="Peça não encontrada")

    # Salvar mensagem do usuario
    db.table("mensagens").insert({
        "id": str(uuid4()),
        "campanha_id": campanha_id,
        "formato": req.formato,
        "role": "user",
        "conteudo": req.mensagem,
    }).execute()

    # Aplicar edicao via Claude
    resultado = await editar_peca(peca.data, req.mensagem, db, campanha_id)

    # Salvar resposta do assistente
    db.table("mensagens").insert({
        "id": str(uuid4()),
        "campanha_id": campanha_id,
        "formato": req.formato,
        "role": "assistant",
        "conteudo": resultado["mensagem_assistente"],
    }).execute()

    return resultado
