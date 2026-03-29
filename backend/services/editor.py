"""Edição conversacional de peças via Anthropic API."""

import os
import json
import base64
from uuid import uuid4
from anthropic import Anthropic
from services.playwright_render import html_to_png

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))


EXEMPLOS_EDICAO = """
Exemplos de interpretação:
- "Aumenta a logo do empreendimento" → Encontrar img da logo e aumentar height em ~30%
- "Muda o CTA para vermelho" → Encontrar .cta ou button e alterar background-color
- "O nome do executivo está pequeno" → Aumentar font-size do .exec-name
- "Troca o headline" → Substituir texto do .headline
- "Aumenta a foto do executivo" → Aumentar width/height da .exec-foto
- "Muda a paleta para azul" → Atualizar cores CSS
- "Remove o subtítulo" → Aplicar display:none no .subtitle
- "Centraliza o bloco do executivo" → Alterar justify-content ou text-align
"""


async def editar_peca(peca: dict, mensagem: str, db, campanha_id: str) -> dict:
    """Aplica edição por linguagem natural no HTML da peça."""

    formato = peca["formato"]
    html_atual = peca["html"]

    prompt = f"""Você é um editor de HTML para peças de marketing imobiliário.
Receba o HTML abaixo e aplique a seguinte alteração: {mensagem}

{EXEMPLOS_EDICAO}

Regras:
- Retorne APENAS o HTML modificado, sem explicações
- Mantenha todas as dimensões e estrutura
- Preserve todas as imagens em base64
- Aplique apenas o que foi pedido, não mude o resto

HTML atual:
{html_atual}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    html_editado = response.content[0].text.strip()

    # Limpar possíveis code blocks
    if html_editado.startswith("```"):
        html_editado = html_editado.split("\n", 1)[1]
    if html_editado.endswith("```"):
        html_editado = html_editado.rsplit("```", 1)[0]

    # Regenerar PNG (exceto email)
    arquivo_url = peca.get("arquivo_url", "")
    if formato != "email":
        largura = 1080
        altura = 1920 if formato == "story" else 1080
        png_path = html_to_png(html_editado, largura, altura)

        # Upload para Supabase Storage
        with open(png_path, "rb") as f:
            png_data = f.read()
        storage_path = f"campanhas/{campanha_id}/{formato}_v{peca['versao'] + 1}.png"
        db.storage.from_("campanhas").upload(
            storage_path, png_data, {"content-type": "image/png"}
        )
        arquivo_url = db.storage.from_("campanhas").get_public_url(storage_path)

        os.remove(png_path)

    # Marcar peça antiga como não-atual
    db.table("pecas").update({"is_atual": False}).eq("id", peca["id"]).execute()

    # Criar nova versão
    nova_peca = {
        "id": str(uuid4()),
        "campanha_id": campanha_id,
        "formato": formato,
        "versao": peca["versao"] + 1,
        "html": html_editado,
        "arquivo_url": arquivo_url,
        "is_atual": True,
    }
    db.table("pecas").insert(nova_peca).execute()

    return {
        "peca": nova_peca,
        "mensagem_assistente": f"Pronto! Apliquei a alteração: {mensagem}. A peça foi atualizada para a versão {nova_peca['versao']}.",
    }
