"""Geração completa de campanha — monta HTMLs, gera PNGs, salva no banco."""

import os
import base64
from uuid import uuid4
from jinja2 import Environment, FileSystemLoader
from services.copy_writer import gerar_copy
from services.image_utils import get_b64, make_white_logo, precisa_inverter_logo, encode_exec_photo
from services.playwright_render import html_to_png

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


async def coletar_assets(url_site: str) -> dict:
    """Coleta logos e imagens do site do cliente via scraping.

    Estratégias (em ordem):
    1. Busca <img> com class/alt contendo logo/brand/marca
    2. Busca <link rel="icon"> ou favicon como fallback
    3. Busca Open Graph image (og:image) para imagem principal
    4. Tenta /favicon.ico como último recurso

    Se falhar, retorna paleta neutra padrão.
    """
    assets = {
        "logo_incorporadora_b64": "",
        "logo_empreendimento_b64": "",
        "imagem_principal_b64": "",
        "cor_primaria": "#C9A96E",
        "cor_fundo": "#0A0A0A",
    }

    if not url_site:
        return assets

    try:
        import httpx
        import re
        from urllib.parse import urljoin

        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url_site)
            html = r.text
            base_url = str(r.url)

            from html.parser import HTMLParser

            logos = []
            og_image = ""
            favicon = ""

            class AssetParser(HTMLParser):
                def handle_starttag(self, tag, attrs):
                    nonlocal og_image, favicon
                    d = dict(attrs)

                    # Strategy 1: <img> with logo-related class/alt/id
                    if tag == "img":
                        src = d.get("src", "")
                        searchable = " ".join([
                            d.get("alt", ""), d.get("class", ""),
                            d.get("id", ""), d.get("data-src", ""),
                        ]).lower()
                        if any(k in searchable for k in ["logo", "brand", "marca", "header-img"]):
                            resolved = urljoin(base_url, src or d.get("data-src", ""))
                            if resolved:
                                logos.append(resolved)

                    # Strategy 2: <link> favicon/icon
                    if tag == "link":
                        rel = d.get("rel", "").lower()
                        if "icon" in rel and d.get("href"):
                            favicon = urljoin(base_url, d["href"])

                    # Strategy 3: og:image
                    if tag == "meta":
                        prop = d.get("property", "").lower()
                        if prop == "og:image" and d.get("content"):
                            og_image = urljoin(base_url, d["content"])

            parser = AssetParser()
            parser.feed(html)

            # Try logos in order
            logo_url = ""
            for candidate in logos:
                try:
                    get_b64(candidate, "image/png")
                    logo_url = candidate
                    break
                except Exception:
                    continue

            # Fallback to favicon
            if not logo_url and favicon:
                logo_url = favicon
            if not logo_url:
                favicon_fallback = urljoin(base_url, "/favicon.ico")
                try:
                    get_b64(favicon_fallback, "image/x-icon")
                    logo_url = favicon_fallback
                except Exception:
                    pass

            if logo_url:
                mime = "image/png" if logo_url.endswith(".svg") or logo_url.endswith(".png") else "image/jpeg"
                assets["logo_incorporadora_b64"] = get_b64(logo_url, mime)
                if precisa_inverter_logo(logo_url, fundo_escuro=True):
                    assets["logo_incorporadora_b64"] = make_white_logo(logo_url)

            # OG image as main image
            if og_image:
                try:
                    assets["imagem_principal_b64"] = get_b64(og_image, "image/jpeg")
                except Exception:
                    pass

    except Exception:
        pass

    return assets


async def gerar_campanha_completa(briefing: dict, executivo: dict, db, campanha_id: str) -> dict:
    """Gera todas as peças de uma campanha."""

    # 1. Gerar copy com Claude
    copy = await gerar_copy(briefing, executivo)

    # 2. Coletar assets do site do cliente
    assets = await coletar_assets(briefing.get("url_site", ""))

    # 3. Preparar foto do executivo
    foto_exec_b64 = ""
    if executivo.get("foto_url"):
        try:
            foto_exec_b64 = get_b64(executivo["foto_url"], "image/jpeg")
            foto_exec_b64 = encode_exec_photo(foto_exec_b64)
        except Exception:
            pass

    # Dados comuns para todos os templates
    dados = {
        "cliente": briefing.get("cliente", ""),
        "empreendimento": briefing.get("empreendimento", ""),
        "executivo_nome": executivo.get("nome", ""),
        "executivo_cargo": f"{executivo.get('cargo', 'Executivo de Parcerias')} · {briefing.get('cliente', '')}",
        "executivo_whatsapp": executivo.get("whatsapp", ""),
        "executivo_email": executivo.get("email", ""),
        "executivo_foto_b64": foto_exec_b64,
        "logo_incorporadora_b64": assets["logo_incorporadora_b64"],
        "logo_empreendimento_b64": assets["logo_empreendimento_b64"],
        "cor_primaria": assets["cor_primaria"],
        "cor_fundo": assets["cor_fundo"],
        "data_evento": briefing.get("data_evento", ""),
        "local_evento": briefing.get("local_evento", ""),
        "url_site": briefing.get("url_site", ""),
    }

    pecas = []

    # 4. Gerar Story (1080x1920)
    story_html = jinja_env.get_template("story.html").render(**dados, copy=copy.get("story", {}))
    story_png_path = html_to_png(story_html, 1080, 1920)
    story_url = await _upload_png(db, campanha_id, "story", story_png_path)
    pecas.append(await _salvar_peca(db, campanha_id, "story", story_html, story_url))

    # 5. Gerar Post (1080x1080)
    post_html = jinja_env.get_template("post.html").render(**dados, copy=copy.get("post", {}))
    post_png_path = html_to_png(post_html, 1080, 1080)
    post_url = await _upload_png(db, campanha_id, "post", post_png_path)
    pecas.append(await _salvar_peca(db, campanha_id, "post", post_html, post_url))

    # 6. Gerar Email
    email_html = jinja_env.get_template("email.html").render(**dados, copy=copy.get("email", {}))
    pecas.append(await _salvar_peca(db, campanha_id, "email", email_html, ""))

    # Salvar copy no banco
    db.table("campanhas").update({"copy": copy}).eq("id", campanha_id).execute()

    return {"pecas": pecas, "copy": copy}


async def _upload_png(db, campanha_id: str, formato: str, png_path: str) -> str:
    """Faz upload do PNG gerado para o Supabase Storage."""
    with open(png_path, "rb") as f:
        data = f.read()
    path = f"campanhas/{campanha_id}/{formato}_v1.png"
    db.storage.from_("campanhas").upload(path, data, {"content-type": "image/png"})
    url = db.storage.from_("campanhas").get_public_url(path)
    os.remove(png_path)
    return url


async def _salvar_peca(db, campanha_id: str, formato: str, html: str, arquivo_url: str) -> dict:
    """Salva uma peça no banco."""
    peca = {
        "id": str(uuid4()),
        "campanha_id": campanha_id,
        "formato": formato,
        "versao": 1,
        "html": html,
        "arquivo_url": arquivo_url,
        "is_atual": True,
    }
    db.table("pecas").insert(peca).execute()
    return peca
