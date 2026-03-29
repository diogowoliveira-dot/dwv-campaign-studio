# DWV Campaign Studio — Especificação Técnica Completa

## Visão geral

Software web para geração e edição conversacional de campanhas imobiliárias. A operadora preenche um briefing, o sistema gera story + post + e-mail, e ela refina as peças por chat até estar satisfeita — exatamente como num conversa com o Claude, mas dentro de uma interface própria da DWV.

---

## Conceito central: editor conversacional

O diferencial do sistema não é só gerar — é **editar por linguagem natural**.

Após a geração inicial, a operadora pode dizer:
- "Aumenta a logo do empreendimento"
- "Muda a cor do CTA para vermelho"
- "O nome do executivo está pequeno, aumenta"
- "Troca o headline para: Exclusivo para corretores"
- "Deixa a foto do executivo maior"

O sistema interpreta o pedido, aplica a mudança no HTML fonte e regera o PNG automaticamente.

---

## Stack técnica

| Camada | Tecnologia | Motivo |
|---|---|---|
| Frontend | Next.js 14 (App Router) | SSR, file upload, fácil deploy Vercel |
| Backend / API | FastAPI (Python) | Já é o que usamos para geração de imagens |
| Geração de imagens | Playwright + Chromium | Testado e validado — converte HTML → PNG |
| IA conversacional | Anthropic API (claude-sonnet-4-5) | Interpreta pedidos e edita o HTML |
| Banco de dados | PostgreSQL (Supabase) | Executivos, campanhas, histórico |
| Storage de arquivos | Supabase Storage | Fotos de executivos, assets gerados |
| Deploy frontend | Vercel | |
| Deploy backend | Railway ou Render | Suporta Playwright/Chromium |
| Autenticação | Supabase Auth | Login por e-mail, sem complexidade |

---

## Arquitetura do sistema

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                    │
│                                                         │
│  /login          /executivos      /campanha/[id]        │
│                                                         │
│  Briefing Form   CRUD executivos  Chat + Preview        │
│  Seleção exec.   Upload de foto   Download arquivos     │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────┐
│                   BACKEND (FastAPI)                      │
│                                                         │
│  POST /campaign/generate     Gera campanha completa     │
│  POST /campaign/edit         Aplica edição por prompt   │
│  GET  /campaign/{id}/files   Retorna arquivos gerados   │
│  CRUD /executivos            Gerencia perfis            │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
┌──────────▼──────────┐   ┌──────────▼──────────┐
│   Anthropic API     │   │  Playwright Engine  │
│   (interpreta       │   │  (HTML → PNG)       │
│    edições e        │   │  1080×1920 story    │
│    gera copy)       │   │  1080×1080 post     │
└─────────────────────┘   └─────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────┐
│                  Supabase                                │
│  Auth · PostgreSQL · Storage                            │
└─────────────────────────────────────────────────────────┘
```

---

## Telas do sistema

### 1. Login
- E-mail + senha
- Autenticação via Supabase Auth
- Redirect para `/dashboard`

### 2. Dashboard
- Botão "Nova campanha"
- Listagem de campanhas recentes (nome cliente, data, status)
- Acesso ao cadastro de executivos

### 3. Cadastro de executivos (`/executivos`)
- Listagem com busca por nome/região
- Formulário: nome, cargo, WhatsApp, e-mail, região
- Upload de foto (recorte automático para quadrado centrado no rosto)
- Ativar / desativar (sem apagar)
- Dados salvos no PostgreSQL, foto no Supabase Storage

### 4. Nova campanha (`/campanha/nova`)

**Passo 1 — Briefing**
```
Tipo de campanha:  [lançamento ▼]
Cliente:           [Sunprime          ]
URL do site:       [sunprime.com.br   ]  → coleta logos automaticamente
Executivo:         [Diogo Westphal ▼  ]
Copy / mensagem:   [textarea          ]
Data do evento:    [02/04/2025  19:00 ]  (visível só se tipo = evento)
[Gerar campanha →]
```

**Passo 2 — Chat + Preview**
Interface dividida em duas colunas:
- Esquerda: chat conversacional
- Direita: preview das peças (story / post / e-mail em abas)

A operadora vê o resultado gerado e refina por mensagem.

### 5. Campanha existente (`/campanha/[id]`)
- Mesma interface de chat + preview
- Histórico de mensagens persistido
- Botões de download individuais por peça

---

## Fluxo de geração

### Geração inicial

```python
# 1. Receber briefing do frontend
briefing = {
    "tipo": "evento",
    "cliente": "Sunprime",
    "empreendimento": "Orgânica",
    "url_site": "https://www.sunprime.com.br",
    "executivo_id": "uuid-do-executivo",
    "copy_base": "Evento de lançamento exclusivo para corretores",
    "data_evento": "02/04/2025 19:00",
    "local_evento": "Meia Praia, Itapema/SC"
}

# 2. Buscar executivo no banco
executivo = db.get_executivo(briefing["executivo_id"])
# {nome, cargo, whatsapp, email, foto_url (Supabase Storage)}

# 3. Coletar assets via web_fetch (logo incorporadora, logo produto, imagem)
assets = coletar_assets(briefing["url_site"])

# 4. Gerar copy com Claude API
copy = gerar_copy(briefing, executivo)
# {story: {headline, subtitulo, cta}, post: {headline, subtitulo, legenda}, email: {assunto, corpo}}

# 5. Montar HTMLs
html_story = montar_story(briefing, copy.story, executivo, assets)
html_post  = montar_post(briefing, copy.post, executivo, assets)
html_email = montar_email(briefing, copy.email, executivo, assets)

# 6. Converter para PNG via Playwright
png_story = html_to_png(html_story, 1080, 1920)
png_post  = html_to_png(html_post,  1080, 1080)

# 7. Salvar tudo no Supabase Storage
# 8. Retornar URLs + HTMLs fonte para o frontend
```

### Edição conversacional

```python
# Receber mensagem da operadora
mensagem = "Aumenta a logo do empreendimento e muda o CTA para vermelho"

# HTML atual da peça que está sendo editada
html_atual = campanha.html_story  # ou html_post, html_email

# Chamar Claude API para aplicar a edição
prompt_edicao = f"""
Você é um editor de HTML para peças de marketing imobiliário.
Receba o HTML abaixo e aplique a seguinte alteração: {mensagem}

Regras:
- Retorne APENAS o HTML modificado, sem explicações
- Mantenha todas as dimensões e estrutura
- Preserve todas as imagens em base64
- Aplique apenas o que foi pedido, não mude o resto

HTML atual:
{html_atual}
"""

html_editado = claude_api(prompt_edicao)

# Regenerar PNG
png_novo = html_to_png(html_editado, largura, altura)

# Salvar nova versão
campanha.salvar_versao(html_editado, png_novo)
```

---

## Modelo de dados (PostgreSQL)

```sql
-- Usuários (gerenciado pelo Supabase Auth)

-- Executivos
CREATE TABLE executivos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    cargo TEXT DEFAULT 'Executivo de Parcerias',
    regiao TEXT,
    whatsapp TEXT,
    email TEXT,
    foto_url TEXT,  -- URL no Supabase Storage
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

-- Campanhas
CREATE TABLE campanhas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES auth.users,
    executivo_id UUID REFERENCES executivos,
    tipo TEXT,              -- lançamento, case, educativo, evento
    cliente TEXT,
    empreendimento TEXT,
    status TEXT DEFAULT 'rascunho',  -- rascunho, gerada, aprovada
    briefing JSONB,         -- todos os dados do briefing
    copy JSONB,             -- copy gerada por formato
    criada_em TIMESTAMPTZ DEFAULT NOW(),
    atualizada_em TIMESTAMPTZ DEFAULT NOW()
);

-- Versões das peças (histórico de edições)
CREATE TABLE pecas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campanha_id UUID REFERENCES campanhas,
    formato TEXT,           -- story, post, email
    versao INTEGER DEFAULT 1,
    html TEXT,              -- HTML fonte completo
    arquivo_url TEXT,       -- URL do PNG/HTML no Storage
    is_atual BOOLEAN DEFAULT TRUE,
    criada_em TIMESTAMPTZ DEFAULT NOW()
);

-- Histórico do chat por campanha
CREATE TABLE mensagens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campanha_id UUID REFERENCES campanhas,
    formato TEXT,           -- story, post, email, geral
    role TEXT,              -- user, assistant
    conteudo TEXT,
    criada_em TIMESTAMPTZ DEFAULT NOW()
);
```

---

## API do backend (FastAPI)

```
POST   /auth/login
POST   /auth/logout

GET    /executivos              Lista todos ativos
POST   /executivos              Cria novo executivo
PUT    /executivos/{id}         Atualiza executivo
PATCH  /executivos/{id}/toggle  Ativa/desativa
POST   /executivos/{id}/foto    Upload de foto

POST   /campanhas               Cria nova campanha (retorna id)
GET    /campanhas               Lista campanhas do usuário
GET    /campanhas/{id}          Dados completos da campanha
POST   /campanhas/{id}/gerar    Dispara geração completa
POST   /campanhas/{id}/editar   Aplica edição por prompt
GET    /campanhas/{id}/arquivos Download dos arquivos gerados
```

---

## Conhecimento técnico validado (trazer do zero)

Toda a lógica abaixo foi **testada e validada** neste projeto. O Claude Code deve implementar exatamente esses padrões:

### Geração de imagens

```python
from playwright.sync_api import sync_playwright

def html_to_png(html: str, width: int, height: int, output_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        # Salvar HTML em arquivo temporário (não usar page.set_content — fontes não carregam)
        tmp_path = f"/tmp/render_{uuid4()}.html"
        with open(tmp_path, "w") as f:
            f.write(html)
        page.goto(f"file://{tmp_path}")
        page.wait_for_timeout(3000)  # CRÍTICO: aguarda Google Fonts
        page.screenshot(path=output_path, full_page=False)
        browser.close()
```

### Imagens sempre em base64

```python
import urllib.request, base64, numpy as np, io
from PIL import Image

headers = {'User-Agent': 'Mozilla/5.0'}

def get_b64(url: str, mime: str) -> str:
    """Baixa imagem e retorna data URI base64."""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return f"data:{mime};base64," + base64.b64encode(r.read()).decode()

def make_white_logo(url: str) -> str:
    """Converte logo escura para branca preservando transparência."""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        data = r.read()
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    arr = np.array(img)
    arr[:,:,0] = 255; arr[:,:,1] = 255; arr[:,:,2] = 255
    buf = io.BytesIO()
    Image.fromarray(arr, "RGBA").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def encode_exec_photo(foto_b64: str) -> str:
    """Recorta quadrado centrado no rosto, 300×300px."""
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
```

### Detecção automática de cor da logo

```python
def precisa_inverter_logo(url: str, fundo_escuro: bool = True) -> bool:
    """Retorna True se a logo deve ser convertida para branca."""
    if not fundo_escuro:
        return False
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        img = Image.open(io.BytesIO(r.read())).convert("RGBA")
    arr = np.array(img)
    opaque = arr[arr[:,:,3] > 128]
    if len(opaque) == 0:
        return False
    media_rgb = opaque[:, :3].mean()
    return media_rgb < 128  # escuro = True
```

---

## Tamanhos mínimos obrigatórios (validados)

| Elemento | Story | Post | E-mail |
|---|---|---|---|
| Logo incorporadora | 52px | 36px | 44px |
| Logo empreendimento | 130–140px | 110px | 64px |
| Foto executivo | 96px | 72px | 60px |
| Nome executivo | 28px bold | 20px bold | 17px bold |
| Contato executivo | 22px | 18px | 14px |

### Bloco do executivo — estrutura validada

```css
.exec-block {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 28px 36px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(201,169,110,0.2);
  border-radius: 4px;
}
/* Separador vertical entre foto e texto */
.exec-divider {
  width: 1px;
  height: 80px;
  background: rgba(201,169,110,0.25);
  flex-shrink: 0;
}
```

---

## Regras de negócio críticas

1. **Cargo do executivo nas peças:** sempre `{cargo} · {nome_da_incorporadora}` — ex: "Executivo de Parcerias · Sunprime". **Nunca** referenciar DWV nas peças de campanha.

2. **Rodapé do e-mail:** sempre logo + site da incorporadora cliente. Nunca logo DWV.

3. **Fotos:** sempre base64. Nunca URLs externas no HTML que será renderizado pelo Playwright.

4. **wait_for_timeout(3000):** obrigatório no Playwright para Google Fonts carregar. Não reduzir.

5. **Logo escura em fundo escuro:** detectar automaticamente e converter para branca via `make_white_logo`.

6. **Copy:** nunca inventar dados. Todo texto vem do briefing ou da API Claude.

7. **Palavras proibidas na copy:** "incrível", "imperdível", "oportunidade única", "sonho realizado".

---

## Identidade visual DWV (para o próprio sistema)

Interface do software usa a identidade DWV:
- Fundo: `#080808`
- Vermelho: `#E8392A`
- Branco: `#FFFFFF`
- Logo: `https://site.dwvapp.com.br/wp-content/uploads/2025/07/cropped-cropped-Prancheta-1@2x-8.png`

---

## Paleta de cores padrão por cliente

Se o usuário não informar cores, o sistema sugere automaticamente baseado nas cores coletadas via `web_fetch` do site do cliente.

Se não conseguir coletar: usar paleta neutra padrão:
- Fundo: `#0A0A0A`
- Primária: `#C9A96E` (dourado)
- Texto: `#FFFFFF`

---

## Fluxo de edição conversacional — exemplos de interpretação

O backend deve passar esses exemplos ao Claude API como few-shot para edição:

```
"Aumenta a logo do empreendimento"
→ Encontrar `.logo-org` ou `img[class*="organica"]` e aumentar height em ~30%

"Muda o CTA para vermelho"
→ Encontrar `.cta` ou `button` e alterar background-color

"O nome do executivo está pequeno"
→ Encontrar `.exec-name` e aumentar font-size para 28-32px

"Troca o headline"
→ Encontrar `.headline` e substituir o texto interno

"Aumenta a foto do executivo"
→ Encontrar `.exec-foto` e aumentar width/height

"Muda a paleta para azul e branco"
→ Atualizar todas as variáveis CSS --cor_primaria e usos diretos da cor atual

"Remove o subtítulo"
→ Encontrar `.subtitle` ou `.tagline` e aplicar display:none

"Centraliza o bloco do executivo"
→ Alterar justify-content ou text-align do bloco
```

---

## Estrutura de pastas do projeto

```
dwv-campaign-studio/
├── frontend/                   # Next.js
│   ├── app/
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── executivos/
│   │   └── campanha/
│   │       ├── nova/
│   │       └── [id]/
│   ├── components/
│   │   ├── ChatPanel.tsx
│   │   ├── PreviewPanel.tsx
│   │   ├── BriefingForm.tsx
│   │   └── ExecutivoCard.tsx
│   └── lib/
│       └── api.ts
│
├── backend/                    # FastAPI
│   ├── main.py
│   ├── routers/
│   │   ├── campanhas.py
│   │   └── executivos.py
│   ├── services/
│   │   ├── generator.py        # Lógica de geração HTML
│   │   ├── playwright_render.py
│   │   ├── image_utils.py      # get_b64, make_white_logo, encode_exec_photo
│   │   ├── copy_writer.py      # Geração de copy via Claude API
│   │   └── editor.py           # Edição conversacional via Claude API
│   ├── templates/
│   │   ├── story.html.jinja    # Template story com variáveis
│   │   ├── post.html.jinja     # Template post
│   │   └── email.html.jinja    # Template e-mail
│   └── models/
│       └── schemas.py
│
└── supabase/
    └── migrations/
        └── 001_initial.sql
```

---

## Prompt de partida para o Claude Code

Cole este prompt ao iniciar o projeto no Claude Code:

```
Quero construir o DWV Campaign Studio — um software web para geração e edição 
conversacional de campanhas imobiliárias.

Tenho uma especificação técnica completa em DWV_CAMPAIGN_STUDIO_SPEC.md que 
contém:
- Arquitetura completa (Next.js + FastAPI + Supabase + Playwright)
- Todo o código Python validado para geração de imagens
- Templates HTML validados para story (1080×1920), post (1080×1080) e e-mail
- Modelo de dados PostgreSQL
- Regras de negócio e tamanhos mínimos já testados
- Fluxo de edição conversacional por prompt

Leia o arquivo spec completo antes de começar e siga rigorosamente os padrões 
técnicos validados — especialmente o uso de base64 para imagens, 
wait_for_timeout(3000) no Playwright, e os tamanhos mínimos de logo e executivo.

Comece criando a estrutura de pastas e o ambiente de desenvolvimento.
```
```
