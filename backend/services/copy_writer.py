"""Geração de copy via Anthropic API — skills de copywriter profissional."""

import os
import json
import httpx

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

PALAVRAS_PROIBIDAS = ["incrível", "imperdível", "oportunidade única", "sonho realizado",
                       "venha conferir", "não perca", "aproveite"]


async def _call_claude(prompt: str, max_tokens: int = 2000) -> str:
    """Call Claude API and return text response."""
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
        data = response.json()
    text = data["content"][0]["text"].strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


async def gerar_copy(briefing: dict, executivo: dict, destaques_site: str = "") -> dict:
    """Gera copy profissional para story, post e email.

    Usa prompts especializados por formato:
    - Story: copywriter de social media (conciso, impactante)
    - Post: copywriter de social media (um pouco mais descritivo)
    - Email: redator de marketing direto (detalhado, persuasivo, informativo)
    """

    contexto_base = f"""BRIEFING DA CAMPANHA:
Tipo: {briefing.get('tipo', 'lancamento')}
Incorporadora: {briefing.get('cliente', '')}
Empreendimento: {briefing.get('empreendimento', '')}
Mensagem/objetivo: {briefing.get('copy_base', '')}
Executivo: {executivo.get('nome', '')} — {executivo.get('cargo', 'Executivo de Parcerias')} · {briefing.get('cliente', '')}
{"Data do evento: " + briefing.get('data_evento', '') if briefing.get('data_evento') else ''}
{"Local: " + briefing.get('local_evento', '') if briefing.get('local_evento') else ''}

{"INFORMAÇÕES DO SITE DO EMPREENDIMENTO:" + chr(10) + destaques_site if destaques_site else ''}

REGRAS ABSOLUTAS:
- Cargo do executivo: "{executivo.get('cargo', 'Executivo de Parcerias')} · {briefing.get('cliente', '')}"
- NUNCA mencionar DWV
- NUNCA inventar dados — use APENAS informações do briefing e do site
- NUNCA usar estas palavras/expressões: {', '.join(PALAVRAS_PROIBIDAS)}
- Se há nomes de arquitetos, paisagistas ou designers mencionados no site, DESTAQUE-OS
- Se há especificações (m², suítes, pavimentos, vagas), USE-AS
- Tom: sofisticado, direto, premium. Linguagem de alto padrão imobiliário."""

    # === STORY (Instagram Story - 1080x1920) ===
    story_prompt = f"""Você é um copywriter sênior especializado em stories de Instagram para o mercado imobiliário de alto padrão.

{contexto_base}

Gere a copy para um STORY vertical (1080x1920). O espaço é limitado — cada palavra conta.

DIRETRIZES DE STORY:
- Headline: máximo 6 palavras. Deve criar curiosidade ou exclusividade. Nada genérico.
- Subtítulo: máximo 12 palavras. Complementa o headline com um dado concreto do empreendimento.
- CTA: máximo 3 palavras. Verbo de ação direto.
- Use dados reais: se o site menciona "29 pavimentos" ou "4 suítes", USE no subtítulo.
- O headline deve soar como algo que um corretor pararia para ler.

Retorne APENAS este JSON:
{{"headline": "...", "subtitulo": "...", "cta": "..."}}"""

    # === POST (Instagram Feed - 1080x1080) ===
    post_prompt = f"""Você é um copywriter sênior especializado em posts de Instagram para o mercado imobiliário de alto padrão.

{contexto_base}

Gere a copy para um POST quadrado (1080x1080). Mais espaço que story, mas ainda visual.

DIRETRIZES DE POST:
- Headline: máximo 8 palavras. Frase de impacto que destaque o diferencial principal.
- Subtítulo: máximo 18 palavras. Inclua especificações reais (metragem, suítes, assinatura arquitetônica).
- Legenda: texto para a legenda do Instagram, máximo 200 caracteres. Inclua chamada para ação.
- Se há arquitetos renomados, mencione no subtítulo.
- Use linguagem que transmita exclusividade e sofisticação.

Retorne APENAS este JSON:
{{"headline": "...", "subtitulo": "...", "legenda": "..."}}"""

    # === EMAIL (Marketing direto - 600px) ===
    email_prompt = f"""Você é um redator de email marketing especializado no mercado imobiliário de alto padrão.
Você escreve como os melhores redatores de marcas como Cyrela, JHSF e Fasano.

{contexto_base}

Gere a copy para um EMAIL MARKETING profissional. Aqui você tem espaço para contar uma história.

DIRETRIZES DE EMAIL:
- Assunto: máximo 50 caracteres. Deve gerar abertura. Pode usar o nome do empreendimento.
- Preview: texto que aparece na inbox, máximo 80 caracteres.
- Título: frase principal do email, aspiracional e direta.
- Corpo: 3-4 parágrafos em HTML (<p>). DEVE incluir:
  * Parágrafo 1: Abertura que posicione o empreendimento como exclusivo. Mencione a incorporadora.
  * Parágrafo 2: Detalhes do produto — use TODOS os dados disponíveis: metragem, suítes, pavimentos,
    vagas, vista. Se houver nomes de arquitetos, paisagistas ou designers, DESTAQUE com <strong>.
  * Parágrafo 3: Proposta de valor para o corretor — por que ele deveria se interessar.
  * Parágrafo 4 (se evento): Detalhes do evento com urgência.
- CTA: texto do botão, máximo 4 palavras.
- Cada <p> deve ter style="margin:0 0 16px;font-size:16px;line-height:1.75;color:rgba(255,255,255,0.65);font-family:Arial,sans-serif;"
- Nomes próprios e dados numéricos em <strong style="color:#fff">

Retorne APENAS este JSON:
{{"assunto": "...", "preview": "...", "titulo": "...", "corpo": "<p>...</p><p>...</p><p>...</p>", "cta": "..."}}"""

    # Execute all 3 in parallel-ish (sequential for API rate limits)
    story_text = await _call_claude(story_prompt, 500)
    post_text = await _call_claude(post_prompt, 600)
    email_text = await _call_claude(email_prompt, 2000)

    try:
        story = json.loads(story_text)
    except json.JSONDecodeError:
        story = {"headline": "Exclusivo para parceiros", "subtitulo": briefing.get("empreendimento", ""), "cta": "Saiba mais"}

    try:
        post = json.loads(post_text)
    except json.JSONDecodeError:
        post = {"headline": "Exclusivo para parceiros", "subtitulo": briefing.get("empreendimento", ""), "legenda": ""}

    try:
        email = json.loads(email_text)
    except json.JSONDecodeError:
        email = {"assunto": briefing.get("empreendimento", ""), "preview": "", "titulo": "Um convite exclusivo",
                 "corpo": f"<p>{briefing.get('copy_base', '')}</p>", "cta": "Saiba mais"}

    copy = {
        "story": _validar_copy(story),
        "post": _validar_copy(post),
        "email": _validar_copy(email),
    }

    return copy


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
