"""Geração de copy via Anthropic API."""

import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

PALAVRAS_PROIBIDAS = ["incrível", "imperdível", "oportunidade única", "sonho realizado"]


async def gerar_copy(briefing: dict, executivo: dict) -> dict:
    """Gera copy para story, post e email com base no briefing."""

    prompt = f"""Você é um copywriter profissional de campanhas imobiliárias.

Gere a copy para uma campanha com os seguintes dados:

Tipo: {briefing.get('tipo', 'lancamento')}
Cliente (incorporadora): {briefing.get('cliente', '')}
Empreendimento: {briefing.get('empreendimento', '')}
Mensagem base: {briefing.get('copy_base', '')}
Executivo: {executivo.get('nome', '')} — {executivo.get('cargo', '')}
{"Data do evento: " + briefing.get('data_evento', '') if briefing.get('data_evento') else ''}
{"Local: " + briefing.get('local_evento', '') if briefing.get('local_evento') else ''}

REGRAS:
- Cargo do executivo nas peças: "{executivo.get('cargo', 'Executivo de Parcerias')} · {briefing.get('cliente', '')}"
- NUNCA referenciar DWV nas peças
- NUNCA usar: {', '.join(PALAVRAS_PROIBIDAS)}
- Tom profissional, direto, aspiracional
- CTA claro e objetivo

Retorne um JSON com esta estrutura exata:
{{
  "story": {{
    "headline": "texto principal (max 8 palavras)",
    "subtitulo": "complemento (max 15 palavras)",
    "cta": "texto do botão (max 4 palavras)"
  }},
  "post": {{
    "headline": "texto principal (max 10 palavras)",
    "subtitulo": "complemento (max 20 palavras)",
    "legenda": "legenda do Instagram (max 150 caracteres)"
  }},
  "email": {{
    "assunto": "assunto do email (max 60 caracteres)",
    "preview": "preview text (max 90 caracteres)",
    "titulo": "titulo do email",
    "corpo": "corpo principal em HTML (2-3 parágrafos curtos com <p>)",
    "cta": "texto do botão CTA (max 5 palavras)"
  }}
}}

Retorne APENAS o JSON, sem explicações."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # Limpar possíveis markdown code blocks
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]

    copy = json.loads(text)
    return _validar_copy(copy)


def _validar_copy(copy: dict) -> dict:
    """Remove palavras proibidas de todos os campos de texto da copy."""
    def limpar(texto: str) -> str:
        resultado = texto
        for palavra in PALAVRAS_PROIBIDAS:
            # Case-insensitive replacement
            lower = resultado.lower()
            idx = lower.find(palavra.lower())
            while idx != -1:
                resultado = resultado[:idx] + resultado[idx + len(palavra):]
                resultado = resultado[:idx] + resultado[idx:].lstrip(" ,.")
                lower = resultado.lower()
                idx = lower.find(palavra.lower())
        return resultado.strip()

    def limpar_dict(d: dict) -> dict:
        cleaned = {}
        for k, v in d.items():
            if isinstance(v, str):
                cleaned[k] = limpar(v)
            elif isinstance(v, dict):
                cleaned[k] = limpar_dict(v)
            else:
                cleaned[k] = v
        return cleaned

    return limpar_dict(copy)
