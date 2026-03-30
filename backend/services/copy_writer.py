"""Geração de copy via Anthropic API — skill dwv-copy-writer integrada."""

import os
import json
import httpx

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

PALAVRAS_PROIBIDAS = ["incrível", "imperdível", "oportunidade única", "sonho realizado",
                       "venha conferir", "não perca", "aproveite"]


async def _call_claude(prompt: str, max_tokens: int = 2000) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ""
    async with httpx.AsyncClient(timeout=60) as http:
        response = await http.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
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
        data = response.json()
    text = data["content"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


async def gerar_copy(briefing: dict, executivo: dict, destaques_site: str = "") -> dict:
    """Gera copy seguindo a skill dwv-copy-writer.

    Pipeline: Copy base → Adaptação Story → Adaptação Post → Adaptação Email
    Tom DWV: direto, confiante, profissional, humano. Sem hipérboles.
    """

    contexto = f"""BRIEFING:
Tipo: {briefing.get('tipo', 'lancamento')}
Incorporadora: {briefing.get('cliente', '')}
Empreendimento: {briefing.get('empreendimento', '')}
Mensagem: {briefing.get('copy_base', '')}
Executivo: {executivo.get('nome', '')} — {executivo.get('cargo', 'Executivo de Parcerias')} · {briefing.get('cliente', '')}
{"Data evento: " + briefing.get('data_evento', '') if briefing.get('data_evento') else ''}
{"Local: " + briefing.get('local_evento', '') if briefing.get('local_evento') else ''}
{chr(10) + "DADOS DO SITE:" + chr(10) + destaques_site if destaques_site else ''}

TOM DWV:
- Direto: sem rodeios, sem jargão vazio
- Confiante: números reais, dados concretos, sem hipérboles
- Profissional: linguagem do mercado imobiliário, não de vendas de varejo
- Humano: o executivo assina, não a marca — tom pessoal e acessível
- NUNCA usar: {', '.join(PALAVRAS_PROIBIDAS)}
- NUNCA inventar dados — só usar o que vem do briefing e do site
- NUNCA mencionar DWV"""

    prompt = f"""Você é o copywriter sênior da DWV, especializado em campanhas imobiliárias de alto padrão.

{contexto}

Gere a copy adaptada para TRÊS formatos. Siga EXATAMENTE estas regras:

━━━ STORY (consumido em 1-2 segundos) ━━━
- headline: máx 5 palavras. Impacto tipográfico. Sem ponto final.
- subtitulo: máx 8 palavras. Dado concreto do empreendimento.
- cta: 2-3 palavras. Verbo de ação. Ex: "Fale conosco", "Saiba mais", "Confirme presença"
- tagline: 1 frase curta aspiracional/emocional sobre o empreendimento (opcional, max 8 palavras)

━━━ POST INSTAGRAM (arte + legenda) ━━━
- headline: máx 7 palavras. Na arte, dentro da imagem.
- subtitulo: 1-2 linhas, máx 15 palavras. Complementa headline.
- cta: texto do botão CTA na arte
- legenda: texto completo para a legenda do Instagram (max 200 chars).
  Estrutura: gancho forte → 2-3 frases → bullet points com dados → CTA com instrução

━━━ EMAIL MARKETING (150-400 palavras no corpo) ━━━
- assunto: máx 55 caracteres. Com dado concreto. Nunca caixa alta total.
- preview: máx 90 caracteres. Complementa o assunto.
- titulo: frase aspiracional principal do email.
- corpo: 3-4 parágrafos em HTML com tags <p>. DEVE incluir:
  * P1: Abertura com gancho (2-3 frases)
  * P2: Produto — TODOS os dados disponíveis: m², suítes, pavimentos, vista, arquitetos com <strong>
  * P3: Proposta de valor para o corretor
  * P4 (se evento): urgência + detalhes do evento
  Cada <p> com: style="margin:0 0 16px;font-size:16px;line-height:1.75;color:rgba(255,255,255,0.65);font-family:Arial,sans-serif;"
  Dados em: <strong style="color:#fff">
- cta: texto do botão. Max 4 palavras. Verbo ativo.

Retorne APENAS este JSON (sem markdown, sem explicação):
{{
  "story": {{"headline": "...", "subtitulo": "...", "cta": "...", "tagline": "..."}},
  "post": {{"headline": "...", "subtitulo": "...", "cta": "...", "legenda": "..."}},
  "email": {{"assunto": "...", "preview": "...", "titulo": "...", "corpo": "<p>...</p><p>...</p><p>...</p>", "cta": "..."}}
}}"""

    raw = await _call_claude(prompt, 2500)

    try:
        copy = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            try:
                copy = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                copy = _fallback_copy(briefing)
        else:
            copy = _fallback_copy(briefing)

    # Validate and clean
    for fmt in ("story", "post", "email"):
        if fmt not in copy:
            copy[fmt] = {}
        copy[fmt] = _validar_copy(copy[fmt])

    return copy


def _fallback_copy(briefing: dict) -> dict:
    """Fallback copy when AI fails."""
    emp = briefing.get("empreendimento", "Empreendimento")
    cli = briefing.get("cliente", "")
    return {
        "story": {"headline": f"Conheça o {emp}", "subtitulo": f"Exclusivo para corretores · {cli}", "cta": "Saiba mais"},
        "post": {"headline": f"Conheça o {emp}", "subtitulo": f"Exclusivo para corretores parceiros · {cli}", "cta": "Saiba mais", "legenda": ""},
        "email": {"assunto": f"{emp} — convite exclusivo", "preview": f"Conheça o {emp} em primeira mão",
                  "titulo": "Um convite exclusivo para você",
                  "corpo": f'<p style="margin:0 0 16px;font-size:16px;line-height:1.75;color:rgba(255,255,255,0.65);font-family:Arial,sans-serif;">{briefing.get("copy_base", "")}</p>',
                  "cta": "Saiba mais"},
    }


def _validar_copy(copy: dict) -> dict:
    """Remove palavras proibidas de todos os campos de texto."""
    def limpar(texto: str) -> str:
        resultado = texto
        for palavra in PALAVRAS_PROIBIDAS:
            lower = resultado.lower()
            idx = lower.find(palavra.lower())
            while idx != -1:
                resultado = resultado[:idx] + resultado[idx + len(palavra):]
                resultado = resultado[:idx] + resultado[idx:].lstrip(" ,.")
                lower = resultado.lower()
                idx = lower.find(palavra.lower())
        return resultado.strip()

    cleaned = {}
    for k, v in copy.items():
        if isinstance(v, str):
            cleaned[k] = limpar(v)
        elif isinstance(v, dict):
            cleaned[k] = _validar_copy(v)
        else:
            cleaned[k] = v
    return cleaned
