from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from models.schemas import ExecutivoInput, ExecutivoResponse
from dependencies import get_current_user
from db import get_db

router = APIRouter()


@router.get("", response_model=list[ExecutivoResponse])
async def listar(user: dict = Depends(get_current_user)):
    db = get_db()
    res = db.table("executivos").select("*").eq("ativo", True).order("nome").execute()
    return res.data


@router.post("", response_model=ExecutivoResponse)
async def criar(data: ExecutivoInput, user: dict = Depends(get_current_user)):
    db = get_db()
    row = {
        "id": str(uuid4()),
        "nome": data.nome,
        "cargo": data.cargo,
        "regiao": data.regiao,
        "whatsapp": data.whatsapp,
        "email": data.email,
    }
    res = db.table("executivos").insert(row).execute()
    return res.data[0]


@router.put("/{exec_id}", response_model=ExecutivoResponse)
async def atualizar(exec_id: str, data: ExecutivoInput, user: dict = Depends(get_current_user)):
    db = get_db()
    updates = data.model_dump(exclude_unset=True)
    res = db.table("executivos").update(updates).eq("id", exec_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Executivo não encontrado")
    return res.data[0]


@router.patch("/{exec_id}/toggle", response_model=ExecutivoResponse)
async def toggle(exec_id: str, user: dict = Depends(get_current_user)):
    db = get_db()
    current = db.table("executivos").select("ativo").eq("id", exec_id).single().execute()
    if not current.data:
        raise HTTPException(status_code=404, detail="Executivo não encontrado")
    novo_estado = not current.data["ativo"]
    res = db.table("executivos").update({"ativo": novo_estado}).eq("id", exec_id).execute()
    return res.data[0]


@router.post("/{exec_id}/foto")
async def upload_foto(exec_id: str, foto: UploadFile = File(...), user: dict = Depends(get_current_user)):
    db = get_db()
    conteudo = await foto.read()
    path = f"executivos/{exec_id}/{foto.filename}"

    db.storage.from_("fotos").upload(path, conteudo, {"content-type": foto.content_type or "image/jpeg"})
    url = db.storage.from_("fotos").get_public_url(path)

    db.table("executivos").update({"foto_url": url}).eq("id", exec_id).execute()

    return {"foto_url": url}
