"""Geração completa de campanha — monta HTMLs, gera PNGs, salva no banco."""

import os
import re
import base64
from uuid import uuid4
from urllib.parse import urljoin
from jinja2 import Environment, FileSystemLoader
from services.copy_writer import gerar_copy
from services.image_utils import get_b64, make_white_logo, precisa_inverter_logo, encode_exec_photo, auditar_logo
from services.playwright_render import html_to_png

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _resolve_url(src: str, base: str) -> str:
    """Resolve relative URL to absolute."""
    if not src or src.startswith("data:"):
        return ""
    try:
        if src.startswith("//"):
            return "https:" + src
        if src.startswith("http"):
            return src
        return urljoin(base, src)
    except Exception:
        return ""


def _is_valid_image_url(url: str) -> bool:
    """Check if URL looks like a real image (not tracking pixel, svg icon, etc)."""
    if not url:
        return False
    lower = url.lower()
    # Skip tiny tracking pixels and base64
    if "1x1" in lower or "pixel" in lower or "spacer" in lower:
        return False
    if lower.endswith(".svg") and ("icon" in lower or "arrow" in lower or "chevron" in lower):
        return False
    return True


def _try_download_image(url: str, min_bytes: int = 2000) -> str:
    """Try to download an image, return b64 or empty string. Validates size."""
    if not url:
        return ""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=12) as r:
            content_type = r.headers.get("Content-Type", "image/jpeg")
            if "image" not in content_type and "octet" not in content_type:
                return ""
            data = r.read()
            if len(data) < min_bytes:
                return ""  # Too small — probably icon or broken
            mime = content_type.split(";")[0].strip()
            if "svg" in mime:
                mime = "image/svg+xml"
            elif "image" not in mime:
                mime = "image/jpeg"
            return f"data:{mime};base64," + base64.b64encode(data).decode()
    except Exception:
        return ""


def _extract_colors_from_html(html: str) -> dict:
    """Extract dominant colors from CSS in the HTML."""
    colors = {"primaria": "", "fundo": ""}

    # 1. meta theme-color
    m = re.search(r'<meta\s+[^>]*name\s*=\s*["\']theme-color["\'][^>]*content\s*=\s*["\']([^"\']+)["\']', html, re.I)
    if not m:
        m = re.search(r'<meta\s+[^>]*content\s*=\s*["\']([^"\']+)["\'][^>]*name\s*=\s*["\']theme-color["\']', html, re.I)
    if m:
        colors["primaria"] = m.group(1).strip()

    # 2. CSS custom properties (--primary, --color-primary, --brand, etc)
    primary_patterns = [
        r'--(?:primary|brand|accent|main)[-_]?(?:color)?:\s*([#][0-9a-fA-F]{3,8})',
        r'--color[-_](?:primary|brand|accent):\s*([#][0-9a-fA-F]{3,8})',
    ]
    for pat in primary_patterns:
        m = re.search(pat, html, re.I)
        if m and not colors["primaria"]:
            colors["primaria"] = m.group(1)

    # 3. Most common hex color in CSS (excluding black/white/grey)
    if not colors["primaria"]:
        all_hex = re.findall(r'#([0-9a-fA-F]{6})\b', html)
        color_counts: dict = {}
        for h in all_hex:
            r_val, g_val, b_val = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            # Skip near-black, near-white, greys
            if max(r_val, g_val, b_val) < 40:
                continue
            if min(r_val, g_val, b_val) > 220:
                continue
            if abs(r_val - g_val) < 15 and abs(g_val - b_val) < 15:
                continue
            color_counts[f"#{h}"] = color_counts.get(f"#{h}", 0) + 1
        if color_counts:
            colors["primaria"] = max(color_counts, key=color_counts.get)

    # 4. Background color from body/main
    bg_match = re.search(r'body\s*\{[^}]*background(?:-color)?:\s*([#][0-9a-fA-F]{3,8})', html, re.I)
    if bg_match:
        colors["fundo"] = bg_match.group(1)

    return colors


async def coletar_assets(url_site: str) -> dict:
    """Coleta logos, imagens e cores do site do cliente.

    Estratégias agressivas para SEMPRE encontrar imagens:
    1. HTML parsing: <img>, <picture>, <source>, background-image em style
    2. Regex em todo o HTML: URLs de imagem (.jpg, .png, .webp)
    3. og:image, twitter:image meta tags
    4. Favicon/apple-touch-icon como logo fallback
    5. Cores: theme-color, CSS variables, hex colors mais comuns
    """
    assets = {
        "logo_incorporadora_b64": "",
        "logo_empreendimento_b64": "",
        "imagem_principal_b64": "",
        "cor_primaria": "#C9A96E",
        "cor_fundo": "#0A0A0A",
        "destaques_site": "",
    }

    if not url_site:
        return assets

    try:
        import httpx

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        ) as client:
            r = await client.get(url_site)
            html = r.text
            base_url = str(r.url)

            # ============================================================
            # PHASE 1: Parse all image sources from HTML
            # ============================================================
            logo_candidates = []
            hero_candidates = []
            all_image_urls = []

            # --- Method A: HTML tag parsing ---
            from html.parser import HTMLParser

            og_image = ""
            twitter_image = ""
            apple_icon = ""
            favicon = ""

            class ComprehensiveParser(HTMLParser):
                nonlocal og_image, twitter_image, apple_icon, favicon

                def handle_starttag(self, tag, attrs):
                    nonlocal og_image, twitter_image, apple_icon, favicon
                    d = dict(attrs)

                    # <img> tags
                    if tag == "img":
                        for attr in ["src", "data-src", "data-lazy-src", "data-original", "data-bg", "srcset"]:
                            val = d.get(attr, "")
                            if not val:
                                continue
                            # srcset: take first/largest
                            if attr == "srcset":
                                parts = val.split(",")
                                for part in parts:
                                    url = part.strip().split(" ")[0]
                                    resolved = _resolve_url(url, base_url)
                                    if resolved:
                                        all_image_urls.append(resolved)
                                continue
                            resolved = _resolve_url(val, base_url)
                            if not resolved:
                                continue
                            all_image_urls.append(resolved)

                            # Classify
                            searchable = " ".join([
                                d.get("alt", ""), d.get("class", ""),
                                d.get("id", ""), val
                            ]).lower()
                            if any(k in searchable for k in ["logo", "brand", "marca"]):
                                logo_candidates.append(resolved)
                            elif any(k in searchable for k in ["fachada", "hero", "banner", "building",
                                    "perspectiva", "render", "destaque", "principal", "featured"]):
                                hero_candidates.append(resolved)

                    # <picture>/<source>
                    if tag == "source":
                        srcset = d.get("srcset", "")
                        if srcset:
                            url = srcset.split(",")[0].strip().split(" ")[0]
                            resolved = _resolve_url(url, base_url)
                            if resolved:
                                all_image_urls.append(resolved)

                    # <link> icons
                    if tag == "link":
                        rel = (d.get("rel", "")).lower()
                        href = d.get("href", "")
                        if "apple-touch-icon" in rel and href:
                            apple_icon = _resolve_url(href, base_url)
                        elif "icon" in rel and href:
                            favicon = _resolve_url(href, base_url)

                    # <meta> og/twitter images
                    if tag == "meta":
                        prop = d.get("property", d.get("name", "")).lower()
                        content = d.get("content", "")
                        if prop == "og:image" and content:
                            og_image = _resolve_url(content, base_url)
                        elif prop == "twitter:image" and content:
                            twitter_image = _resolve_url(content, base_url)

                    # Inline style with background-image
                    style = d.get("style", "")
                    if "background" in style:
                        bg_match = re.search(r'url\(["\']?([^"\')\s]+)["\']?\)', style)
                        if bg_match:
                            resolved = _resolve_url(bg_match.group(1), base_url)
                            if resolved:
                                all_image_urls.append(resolved)
                                if tag in ("section", "div", "header"):
                                    hero_candidates.append(resolved)

            parser = ComprehensiveParser()
            parser.feed(html)

            # --- Method B: Regex for image URLs in entire HTML (catches JS-loaded) ---
            url_pattern = re.compile(
                r'(?:https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\'<>]*)?)',
                re.IGNORECASE
            )
            for match in url_pattern.finditer(html):
                url = match.group(0)
                if _is_valid_image_url(url) and url not in all_image_urls:
                    all_image_urls.append(url)

            # --- Method C: CSS background-image in <style> blocks ---
            css_bg_pattern = re.compile(r'background(?:-image)?:\s*url\(["\']?([^"\')\s]+)["\']?\)', re.I)
            for m in css_bg_pattern.finditer(html):
                resolved = _resolve_url(m.group(1), base_url)
                if resolved and resolved not in all_image_urls:
                    all_image_urls.append(resolved)
                    hero_candidates.append(resolved)

            # ============================================================
            # PHASE 2: Download and validate images
            # ============================================================

            # --- LOGO INCORPORADORA ---
            # Try logo candidates first, then apple-touch-icon, then favicon
            logo_sources = logo_candidates + ([apple_icon] if apple_icon else []) + ([favicon] if favicon else [])
            # Also try /favicon.ico as last resort
            logo_sources.append(_resolve_url("/favicon.ico", base_url))

            for logo_url in logo_sources:
                b64 = _try_download_image(logo_url, min_bytes=500)
                if b64:
                    assets["logo_incorporadora_b64"] = b64
                    break

            # --- LOGO EMPREENDIMENTO (second logo candidate) ---
            for logo_url in logo_candidates[1:]:
                if logo_url == logo_sources[0] if logo_sources else "":
                    continue
                b64 = _try_download_image(logo_url, min_bytes=500)
                if b64:
                    assets["logo_empreendimento_b64"] = b64
                    break

            # --- IMAGEM PRINCIPAL (fachada/hero) — MUST find one ---
            hero_sources = []

            # Priority 1: og:image / twitter:image (usually best quality)
            if og_image:
                hero_sources.append(og_image)
            if twitter_image and twitter_image != og_image:
                hero_sources.append(twitter_image)

            # Priority 2: hero candidates from parsing
            hero_sources.extend(hero_candidates)

            # Priority 3: All images, filtered (skip logos, icons, small)
            for img_url in all_image_urls:
                if img_url in logo_candidates:
                    continue
                lower = img_url.lower()
                if any(skip in lower for skip in ["icon", "logo", "avatar", "favicon", ".svg"]):
                    continue
                hero_sources.append(img_url)

            # Try each until we get a valid large image
            for hero_url in hero_sources:
                b64 = _try_download_image(hero_url, min_bytes=5000)  # At least ~5KB = real photo
                if b64:
                    assets["imagem_principal_b64"] = b64
                    break

            # ============================================================
            # PHASE 3: Audit logo colors for contrast
            # ============================================================
            if assets["logo_incorporadora_b64"]:
                assets["logo_incorporadora_b64"] = auditar_logo(
                    assets["logo_incorporadora_b64"], fundo_escuro=True
                )
            if assets["logo_empreendimento_b64"]:
                assets["logo_empreendimento_b64"] = auditar_logo(
                    assets["logo_empreendimento_b64"], fundo_escuro=True
                )

            # ============================================================
            # PHASE 4: Extract colors from the site
            # ============================================================
            site_colors = _extract_colors_from_html(html)
            if site_colors["primaria"]:
                assets["cor_primaria"] = site_colors["primaria"]
            if site_colors["fundo"]:
                assets["cor_fundo"] = site_colors["fundo"]

            # ============================================================
            # PHASE 5: Extract text content for enriched copy
            # ============================================================
            headings = []
            heading_re = re.compile(r'<h[1-3][^>]*>(.*?)</h[1-3]>', re.I | re.DOTALL)
            for m in heading_re.finditer(html):
                text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if text and 3 < len(text) < 200:
                    headings.append(text)

            specs = []
            text_content = re.sub(r'<[^>]+>', ' ', html)
            for pattern in [
                r'(\d+)\s*(?:dormit[óo]rios?|dorms?)',
                r'(\d+)\s*(?:su[íi]tes?)',
                r'(\d+[\.,]?\d*)\s*m[²2]',
                r'(\d+)\s*(?:vagas?|garagens?)',
                r'(\d+)\s*(?:torres?)',
                r'(\d+)\s*(?:andares?|pavimentos?)',
                r'(\d+)\s*(?:unidades?)',
                r'(\d+)\s*(?:quartos?)',
            ]:
                m = re.search(pattern, text_content, re.I)
                if m:
                    specs.append(m.group(0).strip())

            meta_desc = ""
            meta_match = re.search(
                r'<meta\s+[^>]*name\s*=\s*["\']description["\'][^>]*content\s*=\s*["\']([^"\']+)["\']', html, re.I
            ) or re.search(
                r'<meta\s+[^>]*content\s*=\s*["\']([^"\']+)["\'][^>]*name\s*=\s*["\']description["\']', html, re.I
            )
            if meta_match:
                meta_desc = meta_match.group(1).strip()

            destaques = []
            if headings:
                destaques.append("Headlines do site: " + " | ".join(headings[:6]))
            if specs:
                destaques.append("Configurações do imóvel: " + ", ".join(specs))
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
        "tipo": briefing.get("tipo", "lancamento").replace("lancamento", "Pré-lançamento").replace("case", "Case").replace("educativo", "Educativo").replace("evento", "Evento"),
    }

    pecas = []

    async def _gerar_peca(formato, template_name, width, height, copy_key):
        html = jinja_env.get_template(template_name).render(**dados, copy=copy.get(copy_key, {}))
        arquivo_url = ""
        if formato != "email":
            try:
                png_path = html_to_png(html, width, height)
                arquivo_url = await _upload_png(db, campanha_id, formato, png_path)
            except Exception:
                pass
        pecas.append(await _salvar_peca(db, campanha_id, formato, html, arquivo_url))

    await _gerar_peca("story", "story.html", 1080, 1920, "story")
    await _gerar_peca("post", "post.html", 1080, 1080, "post")
    await _gerar_peca("email", "email.html", 600, 900, "email")

    db.table("campanhas").update({"copy": copy}).eq("id", campanha_id).execute()

    return {"pecas": pecas, "copy": copy}


async def _upload_png(db, campanha_id: str, formato: str, png_path: str) -> str:
    with open(png_path, "rb") as f:
        data = f.read()
    path = f"campanhas/{campanha_id}/{formato}_v1.png"
    db.storage.from_("campanhas").upload(path, data, {"content-type": "image/png"})
    url = db.storage.from_("campanhas").get_public_url(path)
    os.remove(png_path)
    return url


async def _salvar_peca(db, campanha_id: str, formato: str, html: str, arquivo_url: str) -> dict:
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
