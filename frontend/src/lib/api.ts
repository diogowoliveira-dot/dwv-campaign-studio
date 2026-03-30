const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEMO_MODE = false;

// Dados demo para funcionar sem backend
const DEMO_EXECUTIVOS: Executivo[] = [
  { id: "exec-1", nome: "Diogo Westphal", cargo: "Executivo de Parcerias", regiao: "Itapema/SC", whatsapp: "(47) 99999-0001", email: "diogo@exemplo.com.br", foto_url: null, ativo: true },
];

const DEMO_CAMPANHAS: Campanha[] = [
  { id: "camp-1", tipo: "lancamento", cliente: "Sunprime", empreendimento: "Orgânica by Sunprime", status: "aprovada", criada_em: "2025-03-28T10:00:00Z" },
  { id: "camp-2", tipo: "evento", cliente: "FG Empreendimentos", empreendimento: "Sky Tower", status: "gerada", criada_em: "2025-03-26T14:00:00Z" },
  { id: "camp-3", tipo: "case", cliente: "Plaenge", empreendimento: "Le Jardin Residence", status: "gerada", criada_em: "2025-03-24T09:30:00Z" },
  { id: "camp-4", tipo: "educativo", cliente: "Yticon", empreendimento: "Horizonte Prime", status: "rascunho", criada_em: "2025-03-22T16:00:00Z" },
  { id: "camp-5", tipo: "lancamento", cliente: "GT Building", empreendimento: "Aurora Beach Living", status: "aprovada", criada_em: "2025-03-20T11:00:00Z" },
];

function gerarDemoPecas(cliente: string, empreendimento: string, corPrimaria: string): Peca[] {
  // Story — 1080x1920 (estilo post do screenshot: fundo escuro, imagem, dados, executivo)
  const storyHtml = `<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:Georgia,serif;background:#0A0A0A;color:#fff;display:flex;flex-direction:column;overflow:hidden;position:relative}
.badge{position:absolute;top:56px;right:56px;font-size:15px;color:#0A0A0A;background:${corPrimaria};padding:10px 24px;font-family:Arial,sans-serif;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
.logo-top{position:absolute;top:56px;left:56px;height:44px;filter:brightness(0) invert(1)}
.gradient{position:absolute;bottom:0;left:0;right:0;height:65%;background:linear-gradient(to top,#0A0A0A 30%,transparent)}
.content{position:absolute;bottom:0;left:0;right:0;padding:0 56px 0}
.emp-name{font-size:22px;color:${corPrimaria};letter-spacing:.2em;text-transform:uppercase;font-family:Arial,sans-serif;margin-bottom:16px}
.headline{font-size:56px;font-weight:700;line-height:1.15;margin-bottom:12px}
.headline em{font-style:normal;color:${corPrimaria}}
.sub{font-size:18px;color:rgba(255,255,255,.55);font-family:Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;margin-bottom:28px}
.stats{display:flex;gap:2px;margin-bottom:36px}
.stat{padding:16px 24px;background:rgba(255,255,255,.06);text-align:center;flex:1}
.stat-val{font-size:32px;font-weight:700;color:${corPrimaria};font-family:Arial,sans-serif}
.stat-lbl{font-size:11px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;font-family:Arial,sans-serif;margin-top:4px}
.exec-bar{display:flex;align-items:center;padding:28px 32px;background:rgba(255,255,255,.04);border-top:1px solid rgba(255,255,255,.08);margin-top:8px}
.avatar{width:56px;height:56px;border-radius:50%;background:#E8392A;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;color:#fff;font-family:Arial,sans-serif;flex-shrink:0;margin-right:16px}
.exec-info{flex:1}
.exec-name{font-size:18px;font-weight:700;margin-bottom:2px}
.exec-role{font-size:13px;color:rgba(255,255,255,.45);font-family:Arial,sans-serif}
.exec-tel{font-size:16px;color:${corPrimaria};font-weight:700;font-family:Arial,sans-serif;margin-top:4px}
.cta-box{padding:20px 32px;background:${corPrimaria};font-size:14px;font-weight:700;color:#0A0A0A;text-transform:uppercase;letter-spacing:.1em;font-family:Arial,sans-serif;text-align:center;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-left:auto}
</style></head>
<body>
<div class="badge">PRE-LANCAMENTO</div>
<div class="gradient"></div>
<div class="content">
  <div class="emp-name">${empreendimento}</div>
  <div class="headline">Exclusivo para<br>corretores <em>parceiros.</em></div>
  <div class="sub">${empreendimento} · ${cliente}</div>
  <div class="stats">
    <div class="stat"><div class="stat-val">Alto</div><div class="stat-lbl">Padrao</div></div>
    <div class="stat"><div class="stat-val">4</div><div class="stat-lbl">Suites</div></div>
    <div class="stat"><div class="stat-val">360°</div><div class="stat-lbl">Vista</div></div>
  </div>
  <div class="exec-bar">
    <div class="avatar">DW</div>
    <div class="exec-info">
      <div class="exec-name">Diogo Westphal</div>
      <div class="exec-role">Executivo de Parcerias · ${cliente}</div>
      <div class="exec-tel">+55 47 99999-0001</div>
    </div>
    <div class="cta-box">QUERO<br>SABER MAIS</div>
  </div>
</div>
</body></html>`;

  // Post — 1080x1080
  const postHtml = `<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1080px;font-family:Georgia,serif;background:#0A0A0A;color:#fff;display:flex;flex-direction:column;overflow:hidden}
.top{padding:44px 48px;display:flex;justify-content:space-between;align-items:center}
.badge{font-size:13px;color:${corPrimaria};border:1px solid ${corPrimaria};padding:8px 18px;font-family:Arial,sans-serif;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
.content{flex:1;display:flex;flex-direction:column;justify-content:flex-end;padding:0 48px 0}
.emp-name{font-size:16px;color:${corPrimaria};letter-spacing:.18em;text-transform:uppercase;font-family:Arial,sans-serif;margin-bottom:14px}
.headline{font-size:44px;font-weight:700;line-height:1.15;margin-bottom:10px}
.headline em{font-style:normal;color:${corPrimaria}}
.sub{font-size:15px;color:rgba(255,255,255,.5);font-family:Arial,sans-serif;letter-spacing:.06em;text-transform:uppercase;margin-bottom:20px}
.stats{display:flex;gap:2px;margin-bottom:0}
.stat{padding:12px 20px;background:rgba(255,255,255,.06);text-align:center;flex:1}
.stat-val{font-size:24px;font-weight:700;color:${corPrimaria};font-family:Arial,sans-serif}
.stat-lbl{font-size:10px;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.1em;font-family:Arial,sans-serif;margin-top:3px}
.exec-bar{display:flex;align-items:center;padding:22px 28px;background:rgba(255,255,255,.04);border-top:1px solid rgba(255,255,255,.08)}
.avatar{width:48px;height:48px;border-radius:50%;background:#E8392A;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:700;color:#fff;font-family:Arial,sans-serif;flex-shrink:0;margin-right:14px}
.exec-info{flex:1}
.exec-name{font-size:16px;font-weight:700;margin-bottom:1px}
.exec-role{font-size:12px;color:rgba(255,255,255,.4);font-family:Arial,sans-serif}
.exec-tel{font-size:14px;color:${corPrimaria};font-weight:700;font-family:Arial,sans-serif;margin-top:2px}
.cta-box{padding:16px 24px;background:${corPrimaria};font-size:12px;font-weight:700;color:#0A0A0A;text-transform:uppercase;letter-spacing:.1em;font-family:Arial,sans-serif;text-align:center;flex-shrink:0}
</style></head>
<body>
<div class="top"><div class="badge">${cliente}</div></div>
<div class="content">
  <div class="emp-name">${empreendimento}</div>
  <div class="headline">Condições especiais<br>para <em>parceiros.</em></div>
  <div class="sub">${empreendimento} · ${cliente}</div>
  <div class="stats">
    <div class="stat"><div class="stat-val">Alto</div><div class="stat-lbl">Padrao</div></div>
    <div class="stat"><div class="stat-val">4</div><div class="stat-lbl">Suites</div></div>
    <div class="stat"><div class="stat-val">360°</div><div class="stat-lbl">Vista</div></div>
  </div>
</div>
<div class="exec-bar">
  <div class="avatar">DW</div>
  <div class="exec-info">
    <div class="exec-name">Diogo Westphal</div>
    <div class="exec-role">Executivo de Parcerias · ${cliente}</div>
    <div class="exec-tel">+55 47 99999-0001</div>
  </div>
  <div class="cta-box">QUERO<br>SABER MAIS</div>
</div>
</body></html>`;

  // Email — padrão real: table layout, Georgia, fundo #f0ede8, corpo #0A0A0A
  const emailHtml = `<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>${empreendimento} | ${cliente}</title></head>
<body style="margin:0;padding:0;background:#f0ede8;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0ede8;">
<tr><td align="center" style="padding:32px 16px;">
<table width="600" cellpadding="0" cellspacing="0" style="background:#0A0A0A;max-width:600px;width:100%;">

  <!-- HEADER -->
  <tr><td align="center" style="padding:36px 40px 28px;">
    <p style="margin:0;font-size:14px;color:${corPrimaria};letter-spacing:.15em;text-transform:uppercase;font-family:Arial,sans-serif;font-weight:700;">${cliente}</p>
  </td></tr>

  <!-- BANNER GRADIENT -->
  <tr><td style="padding:0;height:200px;background:linear-gradient(135deg,rgba(201,169,110,.15),rgba(0,0,0,.6));text-align:center;vertical-align:middle;">
    <p style="font-size:28px;color:${corPrimaria};letter-spacing:.2em;text-transform:uppercase;font-family:Arial,sans-serif;font-weight:700;margin:0;">${empreendimento}</p>
  </td></tr>

  <!-- CORPO -->
  <tr><td style="padding:36px 48px 36px;">
    <h1 style="margin:0 0 20px;font-size:30px;line-height:1.2;color:#FFFFFF;font-weight:700;font-family:Georgia,serif;">
      Um convite exclusivo para conhecer em primeira mao.
    </h1>
    <p style="margin:0 0 16px;font-size:16px;line-height:1.75;color:rgba(255,255,255,0.65);">
      O <strong style="color:#fff">${empreendimento}</strong> e um dos projetos mais aguardados da ${cliente}. Antes da abertura ao mercado, estamos convidando corretores selecionados para conhecer o produto em primeira mao.
    </p>
    <p style="margin:0 0 16px;font-size:16px;line-height:1.75;color:rgba(255,255,255,0.65);">
      Condições especiais de lancamento, tabela diferenciada e comissao atrativa para corretores parceiros.
    </p>

    <!-- CTA -->
    <table cellpadding="0" cellspacing="0" style="margin:28px 0;">
      <tr><td style="background:${corPrimaria};border-radius:4px;">
        <a href="#" style="display:block;padding:16px 40px;font-size:16px;font-weight:700;color:#0A0A0A;text-decoration:none;letter-spacing:.04em;font-family:Arial,sans-serif;">
          Quero saber mais
        </a>
      </td></tr>
    </table>
  </td></tr>

  <!-- DIVISOR -->
  <tr><td style="padding:0 48px;"><hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:0;"></td></tr>

  <!-- ASSINATURA EXECUTIVO -->
  <tr><td style="padding:28px 48px;">
    <p style="margin:0 0 14px;font-size:12px;color:rgba(255,255,255,0.35);letter-spacing:.1em;text-transform:uppercase;font-family:Arial,sans-serif;">Fale diretamente com o responsavel</p>
    <table cellpadding="0" cellspacing="0">
      <tr>
        <td style="padding-right:16px;vertical-align:middle;">
          <table cellpadding="0" cellspacing="0"><tr><td style="width:56px;height:56px;border-radius:50%;background:#E8392A;text-align:center;vertical-align:middle;font-size:18px;font-weight:700;color:#fff;font-family:Arial,sans-serif;">DW</td></tr></table>
        </td>
        <td style="vertical-align:middle;">
          <p style="margin:0;font-size:16px;font-weight:700;color:#FFFFFF;font-family:Georgia,serif;">Diogo Westphal</p>
          <p style="margin:2px 0;font-size:13px;color:rgba(255,255,255,0.45);font-family:Arial,sans-serif;">Executivo de Parcerias · ${cliente}</p>
          <p style="margin:6px 0 2px;font-size:14px;color:${corPrimaria};font-family:Arial,sans-serif;">+55 47 99999-0001</p>
          <p style="margin:0;font-size:14px;color:${corPrimaria};font-family:Arial,sans-serif;">diogo@exemplo.com.br</p>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="padding:20px 48px 28px;background:rgba(0,0,0,0.3);">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="font-size:13px;color:rgba(255,255,255,.35);font-family:Arial,sans-serif;">${cliente}</td>
        <td align="right" style="font-size:11px;color:rgba(255,255,255,0.25);font-family:Arial,sans-serif;">${cliente.toLowerCase().replace(/\s+/g, '')}.com.br</td>
      </tr>
    </table>
  </td></tr>

</table>
</td></tr></table>
</body></html>`;

  return [
    { id: `peca-story-${Date.now()}`, formato: "story", versao: 1, html: storyHtml, arquivo_url: "" },
    { id: `peca-post-${Date.now() + 1}`, formato: "post", versao: 1, html: postHtml, arquivo_url: "" },
    { id: `peca-email-${Date.now() + 2}`, formato: "email", versao: 1, html: emailHtml, arquivo_url: "" },
  ];
}

const DEMO_CORES: Record<string, string> = {
  "camp-1": "#C9A96E",
  "camp-2": "#2563EB",
  "camp-3": "#059669",
  "camp-4": "#D97706",
  "camp-5": "#8B5CF6",
};

function getHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("dwv_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...(options?.headers || {}) },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
    throw new Error(err.detail || `Erro ${res.status}`);
  }
  return res.json();
}

// Executivos
export const executivos = {
  listar: async (): Promise<Executivo[]> => {
    if (DEMO_MODE) return DEMO_EXECUTIVOS;
    return request<Executivo[]>("/executivos");
  },
  criar: async (data: ExecutivoInput): Promise<Executivo> => {
    if (DEMO_MODE) {
      const novo: Executivo = { id: `exec-${Date.now()}`, ...data, foto_url: null, ativo: true };
      DEMO_EXECUTIVOS.push(novo);
      return novo;
    }
    return request<Executivo>("/executivos", { method: "POST", body: JSON.stringify(data) });
  },
  atualizar: async (id: string, data: Partial<ExecutivoInput>): Promise<Executivo> => {
    if (DEMO_MODE) {
      const idx = DEMO_EXECUTIVOS.findIndex((e) => e.id === id);
      if (idx >= 0) Object.assign(DEMO_EXECUTIVOS[idx], data);
      return DEMO_EXECUTIVOS[idx];
    }
    return request<Executivo>(`/executivos/${id}`, { method: "PUT", body: JSON.stringify(data) });
  },
  toggle: async (id: string): Promise<Executivo> => {
    if (DEMO_MODE) {
      const exec = DEMO_EXECUTIVOS.find((e) => e.id === id);
      if (exec) exec.ativo = !exec.ativo;
      return exec!;
    }
    return request<Executivo>(`/executivos/${id}/toggle`, { method: "PATCH" });
  },
  uploadFoto: async (id: string, file: File) => {
    if (DEMO_MODE) {
      const url = URL.createObjectURL(file);
      const exec = DEMO_EXECUTIVOS.find((e) => e.id === id);
      if (exec) exec.foto_url = url;
      return { foto_url: url };
    }
    const token = localStorage.getItem("dwv_token");
    const form = new FormData();
    form.append("foto", file);
    const res = await fetch(`${BASE}/executivos/${id}/foto`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) throw new Error("Erro ao enviar foto");
    return res.json();
  },
};

// Campanhas
export const campanhas = {
  listar: async (): Promise<Campanha[]> => {
    if (DEMO_MODE) return DEMO_CAMPANHAS;
    return request<Campanha[]>("/campanhas");
  },
  obter: async (id: string): Promise<CampanhaCompleta> => {
    if (DEMO_MODE) {
      const camp = DEMO_CAMPANHAS.find((c) => c.id === id) || DEMO_CAMPANHAS[0];
      const cor = DEMO_CORES[camp.id] || "#C9A96E";
      return {
        ...camp,
        briefing: { tipo: camp.tipo, cliente: camp.cliente, empreendimento: camp.empreendimento, url_site: "", executivo_id: "exec-1", copy_base: "" },
        pecas: gerarDemoPecas(camp.cliente, camp.empreendimento, cor),
        mensagens: [],
        executivo: DEMO_EXECUTIVOS[0],
      };
    }
    return request<CampanhaCompleta>(`/campanhas/${id}`);
  },
  criar: async (data: CampanhaInput): Promise<Campanha> => {
    if (DEMO_MODE) {
      const nova: Campanha = { id: `camp-${Date.now()}`, tipo: data.tipo, cliente: data.cliente, empreendimento: data.empreendimento, status: "rascunho", criada_em: new Date().toISOString() };
      DEMO_CAMPANHAS.unshift(nova);
      return nova;
    }
    return request<Campanha>("/campanhas", { method: "POST", body: JSON.stringify(data) });
  },
  gerar: async (id: string): Promise<CampanhaCompleta> => {
    if (DEMO_MODE) {
      const camp = DEMO_CAMPANHAS.find((c) => c.id === id);
      if (camp) camp.status = "gerada";
      return campanhas.obter(id);
    }
    return request<CampanhaCompleta>(`/campanhas/${id}/gerar`, { method: "POST" });
  },
  deletar: async (id: string): Promise<void> => {
    if (DEMO_MODE) {
      const idx = DEMO_CAMPANHAS.findIndex((c) => c.id === id);
      if (idx >= 0) DEMO_CAMPANHAS.splice(idx, 1);
      return;
    }
    await request(`/campanhas/${id}`, { method: "DELETE" });
  },
  editar: async (id: string, mensagem: string, formato: string, html_atual?: string, versao_atual?: number): Promise<EditarResponse> => {
    // Tenta chamar a API Route (que usa Claude API)
    if (html_atual) {
      try {
        const res = await fetch("/api/campanhas/editar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mensagem, formato, html_atual, versao_atual }),
        });
        if (res.ok) {
          return res.json();
        }
      } catch {
        // Fallback para modo demo
      }
    }
    return {
      peca: null as unknown as Peca,
      mensagem_assistente: `Entendi: "${mensagem}". Configure ANTHROPIC_API_KEY nas variáveis de ambiente da Vercel para ativar a edição por IA.`,
    };
  },
};

// Types
export interface Executivo {
  id: string;
  nome: string;
  cargo: string;
  regiao: string;
  whatsapp: string;
  email: string;
  foto_url: string | null;
  ativo: boolean;
}

export interface ExecutivoInput {
  nome: string;
  cargo: string;
  regiao: string;
  whatsapp: string;
  email: string;
}

export interface Campanha {
  id: string;
  tipo: string;
  cliente: string;
  empreendimento: string;
  status: string;
  criada_em: string;
}

export interface CampanhaInput {
  tipo: string;
  cliente: string;
  empreendimento: string;
  url_site: string;
  executivo_id: string;
  copy_base: string;
  data_evento?: string;
  local_evento?: string;
}

export interface Peca {
  id: string;
  formato: string;
  versao: number;
  html: string;
  arquivo_url: string;
}

export interface Mensagem {
  id: string;
  role: "user" | "assistant";
  conteudo: string;
  criada_em: string;
}

export interface CampanhaCompleta extends Campanha {
  briefing: CampanhaInput;
  pecas: Peca[];
  mensagens: Mensagem[];
  executivo: Executivo;
}

export interface EditarResponse {
  peca: Peca;
  mensagem_assistente: string;
}
