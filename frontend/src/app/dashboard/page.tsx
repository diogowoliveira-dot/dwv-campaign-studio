"use client";
import { useState, useEffect } from "react";
import AppShell from "@/components/AppShell";
import { campanhas, Campanha } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [lista, setLista] = useState<Campanha[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    campanhas.listar()
      .then(setLista)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const statusColor: Record<string, string> = {
    rascunho: "bg-slate-700 text-slate-300",
    gerada: "bg-primary/20 text-primary",
    aprovada: "bg-success/20 text-success",
  };

  const tipoIcon: Record<string, string> = {
    lancamento: "rocket_launch",
    case: "star",
    educativo: "school",
    evento: "event",
  };

  return (
    <AppShell
      title="Estúdio de Campanhas"
      subtitle="Campanhas imobiliárias"
      icon="campaign"
      actions={
        <button
          onClick={() => router.push("/campanha/nova")}
          className="p-2 rounded-lg text-primary hover:bg-primary/10 transition-all"
        >
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>add</span>
        </button>
      }
    >
      <div className="px-5 py-6 space-y-4">
        {/* Header com botao */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold">Campanhas</h2>
            <p className="text-xs text-slate-500">{lista.length} campanha{lista.length !== 1 ? "s" : ""}</p>
          </div>
          <button
            onClick={() => router.push("/campanha/nova")}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-xl transition-all shadow-glow"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>add</span>
            Nova campanha
          </button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Lista vazia */}
        {!loading && lista.length === 0 && (
          <div className="text-center py-20">
            <span className="material-symbols-outlined text-slate-700 mb-3 block" style={{ fontSize: 48 }}>
              campaign
            </span>
            <p className="text-slate-500 text-sm">Nenhuma campanha criada</p>
            <p className="text-slate-600 text-xs mt-1">Clique em &ldquo;Nova campanha&rdquo; para começar</p>
          </div>
        )}

        {/* Lista de campanhas */}
        {!loading && lista.map((c) => (
          <button
            key={c.id}
            onClick={() => router.push(`/campanha/${c.id}`)}
            className="w-full bg-card-dark border border-border-dark rounded-2xl p-4 text-left hover:border-white/10 transition-all group"
          >
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-surface rounded-xl flex items-center justify-center flex-shrink-0">
                <span className="material-symbols-outlined text-primary" style={{ fontSize: 20 }}>
                  {tipoIcon[c.tipo] || "campaign"}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold truncate group-hover:text-primary transition-colors">
                    {c.cliente} — {c.empreendimento}
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${statusColor[c.status] || statusColor.rascunho}`}>
                    {c.status}
                  </span>
                  <span className="text-[10px] text-slate-600">
                    {new Date(c.criada_em).toLocaleDateString("pt-BR")}
                  </span>
                </div>
              </div>
              <span className="material-symbols-outlined text-slate-700 group-hover:text-slate-400 transition-colors" style={{ fontSize: 18 }}>
                chevron_right
              </span>
            </div>
          </button>
        ))}
      </div>
    </AppShell>
  );
}
