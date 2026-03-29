-- DWV Campaign Studio — Schema PostgreSQL (Supabase)
-- Execute no SQL Editor do Supabase

-- ============================================================
-- Executivos
-- ============================================================
CREATE TABLE executivos (
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

CREATE INDEX idx_executivos_ativo ON executivos(ativo);
CREATE INDEX idx_executivos_nome ON executivos(nome);

-- ============================================================
-- Campanhas
-- ============================================================
CREATE TABLE campanhas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES auth.users,
    executivo_id UUID REFERENCES executivos,
    tipo TEXT NOT NULL,  -- lancamento, case, educativo, evento
    cliente TEXT NOT NULL,
    empreendimento TEXT DEFAULT '',
    status TEXT DEFAULT 'rascunho',  -- rascunho, gerada, aprovada
    briefing JSONB DEFAULT '{}',
    copy JSONB DEFAULT '{}',
    criada_em TIMESTAMPTZ DEFAULT NOW(),
    atualizada_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campanhas_status ON campanhas(status);
CREATE INDEX idx_campanhas_criada ON campanhas(criada_em DESC);

-- ============================================================
-- Peças (versões das peças geradas)
-- ============================================================
CREATE TABLE pecas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campanha_id UUID REFERENCES campanhas ON DELETE CASCADE,
    formato TEXT NOT NULL,  -- story, post, email
    versao INTEGER DEFAULT 1,
    html TEXT,
    arquivo_url TEXT DEFAULT '',
    is_atual BOOLEAN DEFAULT TRUE,
    criada_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pecas_campanha ON pecas(campanha_id);
CREATE INDEX idx_pecas_atual ON pecas(campanha_id, formato, is_atual);

-- ============================================================
-- Mensagens (histórico do chat conversacional)
-- ============================================================
CREATE TABLE mensagens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campanha_id UUID REFERENCES campanhas ON DELETE CASCADE,
    formato TEXT DEFAULT 'geral',  -- story, post, email, geral
    role TEXT NOT NULL,  -- user, assistant
    conteudo TEXT NOT NULL,
    criada_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mensagens_campanha ON mensagens(campanha_id, criada_em);

-- ============================================================
-- RLS (Row Level Security) — desabilitado para dev
-- Em produção, habilitar e configurar policies adequadas
-- ============================================================

-- ALTER TABLE executivos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE campanhas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE pecas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE mensagens ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Storage Buckets (executar manualmente no Supabase Dashboard)
-- ============================================================
-- 1. Criar bucket "fotos" (público) para fotos de executivos
-- 2. Criar bucket "campanhas" (público) para PNGs gerados

-- INSERT INTO storage.buckets (id, name, public) VALUES ('fotos', 'fotos', true);
-- INSERT INTO storage.buckets (id, name, public) VALUES ('campanhas', 'campanhas', true);
