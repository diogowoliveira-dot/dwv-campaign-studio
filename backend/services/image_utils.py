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


def make_white_logo(url: str) -> str:
    """Converte logo escura para branca preservando transparência."""
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
    return media_rgb < 128


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
