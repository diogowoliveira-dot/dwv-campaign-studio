"""Renderização HTML → PNG via Playwright — código validado."""
from __future__ import annotations

import os
import tempfile
from typing import Optional
from uuid import uuid4
from playwright.sync_api import sync_playwright


def html_to_png(html: str, width: int, height: int, output_path: Optional[str] = None) -> str:
    """Converte HTML para PNG usando Playwright + Chromium.

    IMPORTANTE:
    - Salva HTML em arquivo temp (não usar page.set_content — fontes não carregam)
    - wait_for_timeout(3000) é CRÍTICO para Google Fonts carregar
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), f"render_{uuid4()}.png")

    tmp_html = os.path.join(tempfile.gettempdir(), f"render_{uuid4()}.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"file://{tmp_html}")
        page.wait_for_timeout(3000)  # CRÍTICO: aguarda Google Fonts
        page.screenshot(path=output_path, full_page=False)
        browser.close()

    # Limpar HTML temporário
    try:
        os.remove(tmp_html)
    except OSError:
        pass

    return output_path
