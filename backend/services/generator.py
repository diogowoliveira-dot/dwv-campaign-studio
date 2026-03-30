"""Geração completa de campanha — monta HTMLs, gera PNGs, salva no banco."""

import os
import base64
from uuid import uuid4
from jinja2 import Environment, FileSystemLoader
from services.copy_writer import gerar_copy
from services.image_utils import get_b64, make_white_logo, precisa_inverter_logo, encode_exec_photo, auditar_logo
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
        "destaques_site": "",  # textos extraídos da página para enriquecer copy
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

            # Also collect ALL images for hero/fachada fallback
            all_images = []

            class FullImageParser(HTMLParser):
                def handle_starttag(self, tag, attrs):
                    if tag == "img":
                        d = dict(attrs)
                        src = d.get("src", "") or d.get("data-src", "") or d.get("data-lazy-src", "")
                        if src and not src.startswith("data:"):
                            resolved = urljoin(base_url, src)
                            all_images.append(resolved)

            img_parser = FullImageParser()
            img_parser.feed(html)

            parser = AssetParser()
            parser.feed(html)

            # --- LOGO INCORPORADORA ---
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
                mime = "image/png" if ".svg" in logo_url or ".png" in logo_url else "image/jpeg"
                try:
                    assets["logo_incorporadora_b64"] = get_b64(logo_url, mime)
                    if precisa_inverter_logo(logo_url, fundo_escuro=True):
                        assets["logo_incorporadora_b64"] = make_white_logo(logo_url)
                except Exception:
                    pass

            # --- LOGO EMPREENDIMENTO (second logo found, or another img with project name) ---
            if len(logos) > 1:
                try:
                    assets["logo_empreendimento_b64"] = get_b64(logos[1], "image/png")
                except Exception:
                    pass

            # --- IMAGEM PRINCIPAL (fachada/hero) — ALWAYS try to get one ---
            hero_url = ""

            # Priority 1: og:image
            if og_image:
                hero_url = og_image

            # Priority 2: look for fachada/building keywords in image URLs
            if not hero_url:
                fachada_keywords = ["fachada", "hero", "banner", "building", "render", "perspectiva", "empreendimento"]
                for img_url in all_images:
                    if any(kw in img_url.lower() for kw in fachada_keywords):
                        hero_url = img_url
                        break

            # Priority 3: first large image (skip tiny icons/logos)
            if not hero_url:
                for img_url in all_images:
                    if img_url in logos or "icon" in img_url.lower() or "logo" in img_url.lower():
                        continue
                    # Skip SVGs (usually decorative)
                    if img_url.endswith(".svg"):
                        continue
                    hero_url = img_url
                    break

            if hero_url:
                try:
                    assets["imagem_principal_b64"] = get_b64(hero_url, "image/jpeg")
                except Exception:
                    pass

            # --- AUDITORIA DE LOGOS: garantir contraste com fundo escuro ---
            if assets["logo_incorporadora_b64"]:
                assets["logo_incorporadora_b64"] = auditar_logo(
                    assets["logo_incorporadora_b64"], fundo_escuro=True
                )
            if assets["logo_empreendimento_b64"]:
                assets["logo_empreendimento_b64"] = auditar_logo(
                    assets["logo_empreendimento_b64"], fundo_escuro=True
                )

            # --- EXTRAÇÃO DE CONTEÚDO TEXTUAL DA PÁGINA ---
            import re as _re

            # Extract headings (h1, h2, h3) and highlight text
            headings = []
            heading_re = _re.compile(r'<h[1-3][^>]*>(.*?)</h[1-3]>', _re.IGNORECASE | _re.DOTALL)
            for m in heading_re.finditer(html):
                text = _re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if text and len(text) > 3 and len(text) < 200:
                    headings.append(text)

            # Extract property specs (dormitórios, suítes, m², vagas, etc.)
            specs = []
            spec_patterns = [
                r'(\d+)\s*(?:dormit[óo]rios?|dorms?)',
                r'(\d+)\s*(?:su[íi]tes?)',
                r'(\d+[\.,]?\d*)\s*m[²2]',
                r'(\d+)\s*(?:vagas?|garagens?)',
                r'(\d+)\s*(?:torres?)',
                r'(\d+)\s*(?:andares?|pavimentos?)',
            ]
            text_content = _re.sub(r'<[^>]+>', ' ', html)
            for pattern in spec_patterns:
                m = _re.search(pattern, text_content, _re.IGNORECASE)
                if m:
                    specs.append(m.group(0).strip())

            # Extract meta description
            meta_desc = ""
            meta_match = _re.search(
                r'<meta\s+[^>]*name\s*=\s*["\']description["\'][^>]*content\s*=\s*["\']([^"\']+)["\']',
                html, _re.IGNORECASE
            ) or _re.search(
                r'<meta\s+[^>]*content\s*=\s*["\']([^"\']+)["\'][^>]*name\s*=\s*["\']description["\']',
                html, _re.IGNORECASE
            )
            if meta_match:
                meta_desc = meta_match.group(1).strip()

            destaques = []
            if headings:
                destaques.append("Headlines do site: " + " | ".join(headings[:5]))
            if specs:
                destaques.append("Configurações: " + ", ".join(specs))
            if meta_desc:
                destaques.append("Descrição: " + meta_desc)

            assets["destaques_site"] = "\n".join(destaques)

    except Exception:
        pass

    return assets


async def gerar_campanha_completa(briefing: dict, executivo: dict, db, campanha_id: str) -> dict:
    """Gera todas as peças de uma campanha."""

    # 1. Coletar assets do site do cliente (antes da copy para usar destaques)
    assets = await coletar_assets(briefing.get("url_site", ""))

    # 2. Gerar copy com Claude (enriquecida com dados do site)
    copy = await gerar_copy(briefing, executivo, destaques_site=assets.get("destaques_site", ""))

    # 3. Preparar foto do executivo
    foto_exec_b64 = ""
    if executivo.get("foto_url"):
        foto_url = executivo["foto_url"]
        try:
            if foto_url.startswith("data:"):
                # Already base64 (uploaded directly)
                foto_exec_b64 = encode_exec_photo(foto_url)
            else:
                foto_exec_b64 = get_b64(foto_url, "image/jpeg")
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
        "imagem_principal_b64": assets["imagem_principal_b64"],
    }

    pecas = []

    # Helper: tenta gerar PNG, se falhar salva só HTML
    async def _gerar_peca(formato, template_name, width, height, copy_key):
        html = jinja_env.get_template(template_name).render(**dados, copy=copy.get(copy_key, {}))
        arquivo_url = ""
        if formato != "email":
            try:
                png_path = html_to_png(html, width, height)
                arquivo_url = await _upload_png(db, campanha_id, formato, png_path)
            except Exception:
                pass  # PNG falhou — salva só HTML, preview via iframe
        pecas.append(await _salvar_peca(db, campanha_id, formato, html, arquivo_url))

    # 4. Gerar Story (1080x1920)
    await _gerar_peca("story", "story.html", 1080, 1920, "story")

    # 5. Gerar Post (1080x1080)
    await _gerar_peca("post", "post.html", 1080, 1080, "post")

    # 6. Gerar Email
    await _gerar_peca("email", "email.html", 600, 900, "email")

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
