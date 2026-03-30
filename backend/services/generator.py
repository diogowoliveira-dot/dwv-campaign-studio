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
    """Extract dominant colors from CSS, inline styles, and color attributes."""
    colors = {"primaria": "", "fundo": ""}

    # 1. meta theme-color
    m = re.search(r'<meta\s+[^>]*name="theme-color"[^>]*content="([^"]+)"', html, re.I)
    if not m:
        m = re.search(r'<meta\s+[^>]*content="([^"]+)"[^>]*name="theme-color"', html, re.I)
    if m:
        colors["primaria"] = m.group(1).strip()

    # 2. CSS custom properties
    for pat in [
        r'--(?:primary|brand|accent|main)[-_]?(?:color)?:\s*([#][0-9a-fA-F]{3,8})',
        r'--color[-_](?:primary|brand|accent):\s*([#][0-9a-fA-F]{3,8})',
    ]:
        m = re.search(pat, html, re.I)
        if m and not colors["primaria"]:
            colors["primaria"] = m.group(1)

    # 3. Collect ALL hex colors from CSS + inline styles
    if not colors["primaria"]:
        all_hex = re.findall(r'#([0-9a-fA-F]{6})\b', html)
        for m in re.finditer(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', html):
            r_v, g_v, b_v = int(m.group(1)), int(m.group(2)), int(m.group(3))
            all_hex.append(f"{r_v:02x}{g_v:02x}{b_v:02x}")

        color_counts: dict = {}
        for h in all_hex:
            h = h.lower()
            r_val, g_val, b_val = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            # Skip pure black and pure white
            if r_val + g_val + b_val < 30:
                continue
            if r_val > 240 and g_val > 240 and b_val > 240:
                continue
            # Skip greys (all channels similar)
            if abs(r_val - g_val) < 10 and abs(g_val - b_val) < 10:
                continue
            color_counts[f"#{h}"] = color_counts.get(f"#{h}", 0) + 1
        if color_counts:
            colors["primaria"] = max(color_counts, key=color_counts.get)

    # 4. Background color
    bg_match = re.search(r'body[^{]*\{[^}]*background(?:-color)?:\s*([#][0-9a-fA-F]{3,8})', html, re.I)
    if bg_match:
        colors["fundo"] = bg_match.group(1)

    # 5. If site is predominantly black/white (no accent color found),
    #    use a clean neutral palette
    if not colors["primaria"]:
        # Check if site is dark-themed
        dark_indicators = html.lower().count("background:#000") + html.lower().count("background-color:#000") + html.lower().count("background:black")
        if dark_indicators > 0:
            colors["primaria"] = "#FFFFFF"  # White accent on dark site
            colors["fundo"] = "#000000"
        else:
            colors["primaria"] = "#1a1a1a"  # Dark accent on light site

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
                            # srcset: extract all URLs
                            if attr == "srcset":
                                parts = val.split(",")
                                for part in parts:
                                    url = part.strip().split(" ")[0]
                                    resolved = _resolve_url(url, base_url)
                                    if resolved and _is_valid_image_url(resolved):
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
            # PHASE 2b: Prefer dark/white logo variant if site provides both
            # ============================================================
            # Look for explicit dark variant of logo (for dark backgrounds)
            for img_url in all_image_urls:
                lower = img_url.lower()
                if ("logo" in lower and ("dark" in lower or "white" in lower or "light" in lower or "branca" in lower)):
                    b64 = _try_download_image(img_url, min_bytes=300)
                    if b64:
                        assets["logo_incorporadora_b64"] = b64
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
            # PHASE 5: Deep content extraction for enriched copy
            # ============================================================
            text_content = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.I | re.DOTALL)
            text_content = re.sub(r'<style[^>]*>.*?</style>', ' ', text_content, flags=re.I | re.DOTALL)
            text_content = re.sub(r'<[^>]+>', ' ', text_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()

            # Headings
            headings = []
            for m in re.finditer(r'<h[1-4][^>]*>(.*?)</h[1-4]>', html, re.I | re.DOTALL):
                t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if t and 3 < len(t) < 300:
                    headings.append(t)

            # Specs (all occurrences)
            specs = []
            spec_patterns = [
                (r'(\d+)\s*(?:dormit[óo]rios?|dorms?)', 'dormitórios'),
                (r'(\d+)\s*(?:su[íi]tes?)', 'suítes'),
                (r'(\d+[\.,]?\d*)\s*m[²2]', 'm²'),
                (r'(\d+)\s*(?:vagas?|garagens?)', 'vagas'),
                (r'(\d+)\s*(?:torres?)', 'torres'),
                (r'(\d+)\s*(?:andares?\s+de\s+apartamentos?)', 'andares'),
                (r'(\d+)\s*(?:pavimentos?)', 'pavimentos'),
                (r'(\d+)\s*(?:unidades?|apartamentos?)', 'unidades'),
                (r'(\d+)\s*(?:quartos?)', 'quartos'),
            ]
            for pattern, label in spec_patterns:
                m = re.search(pattern, text_content, re.I)
                if m:
                    specs.append(m.group(0).strip())

            # People (architects, designers, landscapers)
            people = []
            people_patterns = [
                r'(?:arquitet[oa]|designer|paisagis[tm]a)[^.]{0,10}:\s*([A-ZÀ-Ú][a-zà-ú]+ [A-ZÀ-Ú][a-zà-ú]+)',
                r'([A-ZÀ-Ú][a-zà-ú]+ [A-ZÀ-Ú][a-zà-ú]+)\s*(?:é|são)\s*(?:arquitet|designer|paisagis)',
                r'(?:Studio|Estúdio|Escritório)\s+([A-ZÀ-Ú][a-zà-ú]+ [A-ZÀ-Ú][a-zà-ú]+)',
                r'(?:assinad[oa]\s+(?:por|pelo|pela))\s+([A-ZÀ-Ú][^\.,]{3,40})',
                r'(?:projeto\s+(?:de|do|da))\s+[A-Za-zÀ-ú\s]+(?:assinad[oa]\s+(?:por|pelo|pela))\s+([A-ZÀ-Ú][^\.,]{3,40})',
            ]
            for pattern in people_patterns:
                for m in re.finditer(pattern, text_content, re.I):
                    name = m.group(1).strip()
                    if name and len(name) > 5 and name not in people:
                        people.append(name)

            # Descriptive paragraphs (non-trivial text blocks)
            paragraphs = []
            for m in re.finditer(r'<p[^>]*>(.*?)</p>', html, re.I | re.DOTALL):
                t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if len(t) > 40 and len(t) < 500:
                    paragraphs.append(t)

            # Meta description
            meta_desc = ""
            meta_match = re.search(r'<meta\s+[^>]*name="description"[^>]*content="([^"]+)"', html, re.I)
            if not meta_match:
                meta_match = re.search(r'<meta\s+[^>]*content="([^"]+)"[^>]*name="description"', html, re.I)
            if meta_match:
                meta_desc = meta_match.group(1).strip()

            # Build comprehensive destaques
            destaques = []
            if headings:
                destaques.append("HEADLINES DO SITE: " + " | ".join(headings[:8]))
            if specs:
                destaques.append("ESPECIFICAÇÕES: " + ", ".join(specs))
            if people:
                destaques.append("PROFISSIONAIS/ASSINATURAS: " + ", ".join(people))
            if paragraphs:
                destaques.append("TEXTOS DESCRITIVOS DO SITE:\n" + "\n".join(f"- {p}" for p in paragraphs[:6]))
            if meta_desc:
                destaques.append("META DESCRIPTION: " + meta_desc)

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

    # Compute contrast color for primary
    cor_p = assets["cor_primaria"]
    try:
        r_v = int(cor_p[1:3], 16)
        g_v = int(cor_p[3:5], 16)
        b_v = int(cor_p[5:7], 16)
        luminance = (0.299 * r_v + 0.587 * g_v + 0.114 * b_v) / 255
        cor_primaria_texto = "#000000" if luminance > 0.5 else "#FFFFFF"
    except Exception:
        cor_primaria_texto = "#FFFFFF"

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
        "cor_primaria_texto": cor_primaria_texto,
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

        # Quality validation — fix common issues before saving
        html = _validar_html(html, dados)

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


def _validar_html(html: str, dados: dict) -> str:
    """Post-generation quality validation.

    Checks and fixes:
    1. Dark text on dark background → force white
    2. Empty/missing content sections
    3. Broken image references
    4. Contrast issues on CTA buttons
    """
    cor_fundo = dados.get("cor_fundo", "#0A0A0A")
    cor_primaria = dados.get("cor_primaria", "#C9A96E")

    # Determine if background is dark
    try:
        r_f = int(cor_fundo[1:3], 16)
        g_f = int(cor_fundo[3:5], 16)
        b_f = int(cor_fundo[5:7], 16)
        fundo_escuro = (r_f + g_f + b_f) / 3 < 128
    except Exception:
        fundo_escuro = True

    if fundo_escuro:
        # Fix any dark text colors that would be invisible
        # Replace common dark text on dark bg
        html = html.replace("color:#000000", "color:#FFFFFF")
        html = html.replace("color:#1a1a1a", "color:#FFFFFF")
        html = html.replace("color:#333333", "color:rgba(255,255,255,0.7)")
        html = html.replace("color:#333", "color:rgba(255,255,255,0.7)")
        html = html.replace("color:#666666", "color:rgba(255,255,255,0.5)")
        html = html.replace("color:#666", "color:rgba(255,255,255,0.5)")

    # Ensure headline and subtitle are never empty
    html = re.sub(
        r'class="headline">\s*</div>',
        f'class="headline">{dados.get("empreendimento", "")}</div>',
        html
    )
    html = re.sub(
        r'class="subtitle">\s*</div>',
        f'class="subtitle">{dados.get("cliente", "")}</div>',
        html
    )

    # Remove broken image tags (src="" or src without data)
    html = re.sub(r'<img\s+[^>]*src=""\s*[^>]*/?\s*>', '', html)

    return html


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
