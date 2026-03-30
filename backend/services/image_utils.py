"""Utilitários de imagem — código validado no projeto DWV."""

import urllib.request
import base64
import io
import numpy as np
from PIL import Image

HEADERS = {"User-Agent": "Mozilla/5.0 (DWV Campaign Studio)"}


def get_b64(url: str, mime: str = "image/png") -> str:
    """Baixa imagem e retorna data URI base64."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return f"data:{mime};base64," + base64.b64encode(r.read()).decode()


def _b64_to_pil(data_uri: str) -> Image.Image:
    """Converte data URI base64 para PIL Image."""
    _, data = data_uri.split(",", 1)
    return Image.open(io.BytesIO(base64.b64decode(data)))


def _pil_to_b64(img: Image.Image, fmt: str = "PNG") -> str:
    """Converte PIL Image para data URI base64."""
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=90)
    mime = "image/png" if fmt == "PNG" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def make_white_logo(url: str) -> str:
    """Converte logo escura para branca preservando transparência. Aceita URL."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        data = r.read()
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    arr = np.array(img)
    arr[:, :, 0] = 255
    arr[:, :, 1] = 255
    arr[:, :, 2] = 255
    buf = io.BytesIO()
    Image.fromarray(arr, "RGBA").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def make_white_logo_from_b64(data_uri: str) -> str:
    """Converte logo base64 para branca preservando transparência."""
    img = _b64_to_pil(data_uri).convert("RGBA")
    arr = np.array(img)
    arr[:, :, 0] = 255
    arr[:, :, 1] = 255
    arr[:, :, 2] = 255
    return _pil_to_b64(Image.fromarray(arr, "RGBA"), "PNG")


def make_dark_logo_from_b64(data_uri: str) -> str:
    """Converte logo clara para preta preservando transparência."""
    img = _b64_to_pil(data_uri).convert("RGBA")
    arr = np.array(img)
    arr[:, :, 0] = 0
    arr[:, :, 1] = 0
    arr[:, :, 2] = 0
    return _pil_to_b64(Image.fromarray(arr, "RGBA"), "PNG")


def analisar_brilho_logo(data_uri: str) -> float:
    """Retorna brilho médio dos pixels opacos (0=preto, 255=branco)."""
    img = _b64_to_pil(data_uri).convert("RGBA")
    arr = np.array(img)
    opaque = arr[arr[:, :, 3] > 128]
    if len(opaque) == 0:
        return 128.0  # neutro se sem pixels opacos
    return float(opaque[:, :3].mean())


def auditar_logo(data_uri: str, fundo_escuro: bool = True) -> str:
    """Audita e corrige a cor da logo para garantir contraste com o fundo.

    - Fundo escuro (#0A0A0A): logo deve ser branca/clara
    - Fundo claro: logo deve ser preta/escura

    Retorna o data URI corrigido.
    """
    if not data_uri:
        return data_uri

    try:
        brilho = analisar_brilho_logo(data_uri)

        if fundo_escuro:
            # Fundo escuro: logo precisa ser clara (brilho > 150)
            if brilho < 150:
                return make_white_logo_from_b64(data_uri)
        else:
            # Fundo claro: logo precisa ser escura (brilho < 100)
            if brilho > 100:
                return make_dark_logo_from_b64(data_uri)

        return data_uri
    except Exception:
        return data_uri


def precisa_inverter_logo(url: str, fundo_escuro: bool = True) -> bool:
    """Retorna True se a logo deve ser convertida para branca."""
    if not fundo_escuro:
        return False
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        img = Image.open(io.BytesIO(r.read())).convert("RGBA")
    arr = np.array(img)
    opaque = arr[arr[:, :, 3] > 128]
    if len(opaque) == 0:
        return False
    media_rgb = opaque[:, :3].mean()
    return media_rgb < 150


def encode_exec_photo(foto_b64: str) -> str:
    """Recorta quadrado centrado no rosto, 300x300px."""
    header, data = foto_b64.split(",", 1)
    img = Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")
    w, h = img.size
    size = min(w, h)
    left = (w - size) // 2
    top = max(0, int(h * 0.02))
    img = img.crop((left, top, left + size, top + size)).resize((300, 300), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
