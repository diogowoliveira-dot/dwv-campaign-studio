"use client";
import { useState, useEffect } from "react";
import { executivos as execApi, Executivo, CampanhaInput } from "@/lib/api";

interface Props {
  onSubmit: (data: CampanhaInput) => Promise<void>;
}

const tipos = [
  { value: "lancamento", label: "Lançamento", icon: "rocket_launch" },
  { value: "case", label: "Case de sucesso", icon: "star" },
  { value: "educativo", label: "Educativo", icon: "school" },
  { value: "evento", label: "Evento", icon: "event" },
];

export default function BriefingForm({ onSubmit }: Props) {
  const [execs, setExecs] = useState<Executivo[]>([]);
  const [enviando, setEnviando] = useState(false);
  const [form, setForm] = useState<CampanhaInput>({
    tipo: "lancamento",
    cliente: "",
    empreendimento: "",
    url_site: "",
    executivo_id: "",
    copy_base: "",
    data_evento: "",
    local_evento: "",
  });

  useEffect(() => {
    execApi.listar().then((list) => {
      const ativos = list.filter((e) => e.ativo);
      setExecs(ativos);
      if (ativos.length > 0 && !form.executivo_id) {
        setForm((f) => ({ ...f, executivo_id: ativos[0].id }));
      }
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    try {
      await onSubmit(form);
    } finally {
      setEnviando(false);
    }
  };

  const set = (key: keyof CampanhaInput, val: string) =>
    setForm((f) => ({ ...f, [key]: val }));

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Tipo de campanha */}
      <div>
        <label className="text-xs font-medium text-slate-400 mb-2 block">Tipo de campanha</label>
        <div className="grid grid-cols-2 gap-2">
          {tipos.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => set("tipo", t.value)}
              className={`flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium transition-all ${
                form.tipo === t.value
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border-dark bg-surface text-slate-400 hover:border-white/10"
              }`}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Cliente */}
      <div>
        <label className="text-xs font-medium text-slate-400 mb-1.5 block">Cliente (incorporadora)</label>
        <input
          type="text"
          value={form.cliente}
          onChange={(e) => set("cliente", e.target.value)}
          placeholder="Sunprime"
          required
          className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
        />
      </div>

      {/* Empreendimento */}
      <div>
        <label className="text-xs font-medium text-slate-400 mb-1.5 block">Empreendimento</label>
        <input
          type="text"
          value={form.empreendimento}
          onChange={(e) => set("empreendimento", e.target.value)}
          placeholder="Orgânica by Sunprime"
          required
          className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
        />
      </div>

      {/* URL do site */}
      <div>
        <label className="text-xs font-medium text-slate-400 mb-1.5 block">URL do site</label>
        <input
          type="url"
          value={form.url_site}
          onChange={(e) => set("url_site", e.target.value)}
          placeholder="https://www.sunprime.com.br"
          className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
        />
        <p className="text-[10px] text-slate-600 mt-1">Logos e cores serão coletadas automaticamente</p>
      </div>

      {/* Executivo */}
      <div>
        <label className="text-xs font-medium text-slate-400 mb-1.5 block">Executivo responsável</label>
        <select
          value={form.executivo_id}
          onChange={(e) => set("executivo_id", e.target.value)}
          required
          className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm focus:outline-none focus:border-primary/50 transition-all appearance-none"
        >
          <option value="">Selecione...</option>
          {execs.map((e) => (
            <option key={e.id} value={e.id}>{e.nome} — {e.regiao}</option>
          ))}
        </select>
      </div>

      {/* Copy base */}
      <div>
        <label className="text-xs font-medium text-slate-400 mb-1.5 block">Copy / mensagem base</label>
        <textarea
          value={form.copy_base}
          onChange={(e) => set("copy_base", e.target.value)}
          placeholder="Descreva o objetivo da campanha, público-alvo, mensagem principal..."
          rows={4}
          required
          className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all resize-none"
        />
      </div>

      {/* Campos de evento */}
      {form.tipo === "evento" && (
        <div className="space-y-4 p-4 bg-surface/50 border border-border-dark rounded-xl">
          <p className="text-xs font-medium text-primary flex items-center gap-1">
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>event</span>
            Dados do evento
          </p>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Data e hora</label>
            <input
              type="datetime-local"
              value={form.data_evento}
              onChange={(e) => set("data_evento", e.target.value)}
              className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm focus:outline-none focus:border-primary/50 transition-all"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Local</label>
            <input
              type="text"
              value={form.local_evento}
              onChange={(e) => set("local_evento", e.target.value)}
              placeholder="Meia Praia, Itapema/SC"
              className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 transition-all"
            />
          </div>
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={enviando}
        className="w-full py-3.5 bg-primary hover:bg-primary-dark text-white font-semibold text-sm rounded-xl transition-all disabled:opacity-50 shadow-glow flex items-center justify-center gap-2"
      >
        {enviando ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Gerando campanha...
          </>
        ) : (
          <>
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>auto_awesome</span>
            Gerar campanha
          </>
        )}
      </button>
    </form>
  );
}
