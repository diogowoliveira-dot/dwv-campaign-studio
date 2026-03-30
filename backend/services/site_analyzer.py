"""AI-powered site analysis — uses Claude to identify brand colors, fachada images, and key content."""

import os
import re
import httpx
import base64
from urllib.parse import urljoin, urlparse

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


async def _call_claude(prompt: str, max_tokens: int = 1500) -> str:
    async with httpx.AsyncClient(timeout=60) as http:
        response = await http.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"].strip()


def _resolve(src: str, base: str) -> str:
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


def _try_download(url: str, min_bytes: int = 2000) -> tuple:
    """Download image, try path variants. Returns (bytes, content_type) or (None, None)."""
    from urllib.parse import urlparse
    import urllib.request

    urls = [url]
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) > 2:
        urls.append(f"{parsed.scheme}://{parsed.netloc}/{'/'.join(parts[1:])}")
    if len(parts) > 3:
        urls.append(f"{parsed.scheme}://{parsed.netloc}/{'/'.join(parts[2:])}")

    for try_url in urls:
        try:
            req = urllib.request.Request(try_url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            })
            with urllib.request.urlopen(req, timeout=12) as r:
                ct = r.headers.get("Content-Type", "")
                if "image" not in ct and "octet" not in ct:
                    continue
                data = r.read()
                if len(data) < min_bytes:
                    continue
                return data, ct.split(";")[0].strip()
        except Exception:
            continue
    return None, None


async def analisar_site(url_site: str, url_home: str = "") -> dict:
    """Use AI to analyze the site and return structured brand info.

    Returns:
        {
            "cor_primaria": "#hex",
            "cor_fundo": "#hex",
            "fachada_url": "best fachada image URL",
            "logo_url": "best logo URL for dark bg",
            "logo_emp_url": "empreendimento logo URL",
            "destaques": "text content for copy"
        }
    """
    result = {
        "cor_primaria": "#C9A96E",
        "cor_fundo": "#0A0A0A",
        "fachada_url": "",
        "logo_url": "",
        "logo_emp_url": "",
        "destaques": "",
    }

    if not url_site:
        return result

    try:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        ) as client:
            # Fetch the empreendimento page
            r = await client.get(url_site)
            html_emp = r.text
            base_url = str(r.url)

            # Also fetch the home page for brand colors
            if not url_home:
                parsed = urlparse(base_url)
                url_home = f"{parsed.scheme}://{parsed.netloc}/"

            r_home = await client.get(url_home)
            html_home = r_home.text

            # Extract ALL image URLs from both pages
            all_image_urls = []
            for html, base in [(html_emp, base_url), (html_home, url_home)]:
                for m in re.finditer(r'(?:src|data-src|data-lazy-src)="([^"]+)"', html, re.I):
                    resolved = _resolve(m.group(1), base)
                    if resolved and re.search(r'\.(jpg|jpeg|png|webp)', resolved, re.I):
                        if resolved not in all_image_urls:
                            all_image_urls.append(resolved)
                # CSS backgrounds
                for m in re.finditer(r"url\(['\"]?([^'\")\s]+)['\"]?\)", html):
                    resolved = _resolve(m.group(1), base)
                    if resolved and re.search(r'\.(jpg|jpeg|png|webp)', resolved, re.I):
                        if resolved not in all_image_urls:
                            all_image_urls.append(resolved)

            # Extract text content
            text_emp = re.sub(r"<script[^>]*>.*?</script>", " ", html_emp, flags=re.I | re.DOTALL)
            text_emp = re.sub(r"<style[^>]*>.*?</style>", " ", text_emp, flags=re.I | re.DOTALL)
            text_emp = re.sub(r"<[^>]+>", " ", text_emp)
            text_emp = re.sub(r"\s+", " ", text_emp).strip()

            # Headings
            headings = []
            for m in re.finditer(r"<h[1-4][^>]*>(.*?)</h[1-4]>", html_emp, re.I | re.DOTALL):
                t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                if t and 3 < len(t) < 300:
                    headings.append(t)

            # Paragraphs
            paragraphs = []
            for m in re.finditer(r"<p[^>]*>(.*?)</p>", html_emp, re.I | re.DOTALL):
                t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                if 30 < len(t) < 500:
                    paragraphs.append(t)

            # Specs
            specs = []
            for pattern in [
                r'\d+\s*(?:dormit[óo]rios?|dorms?)',
                r'\d+\s*su[íi]tes?',
                r'\d+[\.,]?\d*\s*m[²2]',
                r'\d+\s*vagas?',
                r'\d+\s*(?:torres?|pavimentos?|andares?|unidades?)',
            ]:
                for m in re.finditer(pattern, text_emp, re.I):
                    specs.append(m.group(0).strip())

            # People
            people = []
            for pattern in [
                r'(?:Studio|Estúdio|Escritório)\s+([A-ZÀ-Ú][a-zà-ú]+\s+[A-ZÀ-Ú][a-zà-ú]+)',
                r'(?:arquitet[oa]|designer|paisagis)\w*[^.]{0,10}?([A-ZÀ-Ú][a-zà-ú]+\s+[A-ZÀ-Ú][a-zà-ú]+)',
            ]:
                for m in re.finditer(pattern, text_emp):
                    name = m.group(1).strip()
                    if name and len(name) > 5 and name not in people:
                        people.append(name)

            # Build destaques
            destaques_parts = []
            if headings:
                destaques_parts.append("HEADLINES: " + " | ".join(headings[:6]))
            if specs:
                destaques_parts.append("SPECS: " + ", ".join(specs))
            if people:
                destaques_parts.append("PROFISSIONAIS: " + ", ".join(people))
            if paragraphs:
                destaques_parts.append("TEXTOS:\n" + "\n".join(f"- {p}" for p in paragraphs[:5]))
            result["destaques"] = "\n".join(destaques_parts)

            # === ASK CLAUDE TO ANALYZE ===
            # Classify images and pick brand color
            image_list = "\n".join(f"{i+1}. {url}" for i, url in enumerate(all_image_urls[:25]))

            ai_prompt = f"""Você é um diretor de arte especializado em incorporadoras imobiliárias de alto padrão.

SITE DO EMPREENDIMENTO: {url_site}
HOME DA INCORPORADORA: {url_home}

LISTA DE IMAGENS ENCONTRADAS NO SITE (numere cada uma):
{image_list}

CONTEÚDO TEXTUAL DO SITE:
{text_emp[:2000]}

CORES HEX ENCONTRADAS NO CSS:
{', '.join(set(re.findall(r'#[0-9a-fA-F]{{6}}', html_emp + html_home))[:20]) or 'Nenhuma cor encontrada no CSS'}

ANALISE E RESPONDA:

1. **FACHADA** — Qual número é a imagem da FACHADA/PERSPECTIVA EXTERNA do empreendimento?
   REGRAS:
   - Fachada = renderização ou foto EXTERNA do prédio/edifício inteiro
   - NÃO é: logo, planta baixa, foto de interior, thumbnail, background decorativo
   - Imagens com nome tipo "00122-nome-empreendimento-XXXX.jpg" são fotos do empreendimento — a PRIMEIRA delas geralmente é a fachada
   - Imagens com "full_" no nome são versões grandes (preferíveis)
   - Se houver múltiplas, escolha a que parece ser a fachada principal (geralmente a primeira da sequência)
   - DEVE escolher uma. Se nenhuma parece ser fachada, escolha a primeira imagem grande que não seja logo.

2. **COR PRIMÁRIA DA MARCA** — Qual a cor principal da incorporadora?
   REGRAS:
   - Analise a HOME da incorporadora, não o empreendimento
   - Veja os arquivos de logo: se há "logo.png" e "logo-dark.png", a marca provavelmente é clean (preto/branco)
   - Para marcas preto/branco sem cor accent: use branco #FFFFFF como accent
   - NÃO use cores de classes CSS utilitárias (verde de botão de WhatsApp, azul de link, etc.)
   - A cor deve ser a que aparece como IDENTIDADE VISUAL da marca

3. **LOGO PARA FUNDO ESCURO** — Qual é o logo da incorporadora para usar em fundo preto?
   IMPORTANTE: se existem arquivos "logo-dark" e "logo" normal, o "logo-dark" é a versão BRANCA (para fundo dark). Escolha essa.

4. **LOGO DO EMPREENDIMENTO** — Se existe um logo específico do empreendimento (diferente do logo da incorporadora), qual número?

RESPONDA APENAS ESTE JSON (sem explicação, sem markdown):
{{"fachada": NUMERO, "cor_primaria": "#HEXCOR", "logo": NUMERO, "logo_emp": NUMERO}}"""

            ai_response = await _call_claude(ai_prompt, 300)

            # Parse response — handle various markdown wrappers
            import json
            clean = ai_response
            if "```" in clean:
                # Extract content between code fences
                parts = clean.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        clean = part
                        break
            clean = clean.strip()

            try:
                ai_data = json.loads(clean)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                json_match = re.search(r'\{[^}]+\}', clean)
                if json_match:
                    try:
                        ai_data = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        ai_data = {}
                else:
                    ai_data = {}

            if ai_data.get("cor_primaria"):
                result["cor_primaria"] = ai_data["cor_primaria"]

            fachada_idx = ai_data.get("fachada", 0)
            if fachada_idx and 0 < fachada_idx <= len(all_image_urls):
                result["fachada_url"] = all_image_urls[fachada_idx - 1]

            logo_idx = ai_data.get("logo", 0)
            if logo_idx and 0 < logo_idx <= len(all_image_urls):
                result["logo_url"] = all_image_urls[logo_idx - 1]

            logo_emp_idx = ai_data.get("logo_emp", 0)
            if logo_emp_idx and 0 < logo_emp_idx <= len(all_image_urls):
                result["logo_emp_url"] = all_image_urls[logo_emp_idx - 1]

    except Exception:
        pass

    return result
