-- DWV Campaign Studio — Migration 001: Initial Schema
-- Supabase PostgreSQL

-- ============================================================
-- Executivos
-- ============================================================
CREATE TABLE IF NOT EXISTS executivos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    cargo TEXT DEFAULT 'Executivo de Parcerias',
    regiao TEXT DEFAULT '',
    whatsapp TEXT DEFAULT '',
    email TEXT DEFAULT '',
    foto_url TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_executivos_ativo ON executivos(ativo);
CREATE INDEX IF NOT EXISTS idx_executivos_nome ON executivos(nome);

-- ============================================================
-- Campanhas
-- ============================================================
CREATE TABLE IF NOT EXISTS campanhas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES auth.users,
    executivo_id UUID REFERENCES executivos,
    tipo TEXT NOT NULL,
    cliente TEXT NOT NULL,
    empreendimento TEXT DEFAULT '',
    status TEXT DEFAULT 'rascunho',
    briefing JSONB DEFAULT '{}',
    copy JSONB DEFAULT '{}',
    criada_em TIMESTAMPTZ DEFAULT NOW(),
    atualizada_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campanhas_status ON campanhas(status);
CREATE INDEX IF NOT EXISTS idx_campanhas_criada ON campanhas(criada_em DESC);
CREATE INDEX IF NOT EXISTS idx_campanhas_usuario ON campanhas(usuario_id);

-- ============================================================
-- Peças (versões das peças geradas)
-- ============================================================
CREATE TABLE IF NOT EXISTS pecas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campanha_id UUID REFERENCES campanhas ON DELETE CASCADE,
    formato TEXT NOT NULL,
    versao INTEGER DEFAULT 1,
    html TEXT,
    arquivo_url TEXT DEFAULT '',
    is_atual BOOLEAN DEFAULT TRUE,
    criada_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pecas_campanha ON pecas(campanha_id);
CREATE INDEX IF NOT EXISTS idx_pecas_atual ON pecas(campanha_id, formato, is_atual);

-- ============================================================
-- Mensagens (histórico do chat conversacional)
-- ============================================================
CREATE TABLE IF NOT EXISTS mensagens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campanha_id UUID REFERENCES campanhas ON DELETE CASCADE,
    formato TEXT DEFAULT 'geral',
    role TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    criada_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mensagens_campanha ON mensagens(campanha_id, criada_em);

-- ============================================================
-- Storage Buckets
-- ============================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('fotos', 'fotos', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public)
VALUES ('campanhas', 'campanhas', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- RLS Policies
-- ============================================================
ALTER TABLE campanhas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own campaigns" ON campanhas
    FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "Users insert own campaigns" ON campanhas
    FOR INSERT WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "Users update own campaigns" ON campanhas
    FOR UPDATE USING (auth.uid() = usuario_id);

ALTER TABLE pecas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own pecas" ON pecas
    FOR SELECT USING (
        campanha_id IN (SELECT id FROM campanhas WHERE usuario_id = auth.uid())
    );

ALTER TABLE mensagens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own messages" ON mensagens
    FOR SELECT USING (
        campanha_id IN (SELECT id FROM campanhas WHERE usuario_id = auth.uid())
    );
