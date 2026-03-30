"use client";
import { useState, useEffect } from "react";
import AppShell from "@/components/AppShell";
import { campanhas, Campanha } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [lista, setLista] = useState<Campanha[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroCliente, setFiltroCliente] = useState("");
  const [deletando, setDeletando] = useState<string | null>(null);

  const carregar = () => {
    setLoading(true);
    campanhas.listar()
      .then(setLista)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(carregar, []);

  const handleDeletar = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Tem certeza que deseja deletar esta campanha?")) return;
    setDeletando(id);
    try {
      await campanhas.deletar(id);
      setLista((prev) => prev.filter((c) => c.id !== id));
    } catch {
      alert("Erro ao deletar campanha");
    } finally {
      setDeletando(null);
    }
  };

  // Group by client (incorporadora)
  const clientes = Array.from(new Set(lista.map((c) => c.cliente))).sort();
  const filtradas = filtroCliente
    ? lista.filter((c) => c.cliente === filtroCliente)
    : lista;

  const agrupadas = filtradas.reduce<Record<string, Campanha[]>>((acc, c) => {
    if (!acc[c.cliente]) acc[c.cliente] = [];
    acc[c.cliente].push(c);
    return acc;
  }, {});

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
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold">Campanhas</h2>
            <p className="text-xs text-slate-500">
              {lista.length} campanha{lista.length !== 1 ? "s" : ""}
              {clientes.length > 1 && ` · ${clientes.length} incorporadoras`}
            </p>
          </div>
          <button
            onClick={() => router.push("/campanha/nova")}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-xl transition-all shadow-glow"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>add</span>
            Nova campanha
          </button>
        </div>

        {/* Filtro por incorporadora */}
        {clientes.length > 1 && (
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
            <button
              onClick={() => setFiltroCliente("")}
              className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                !filtroCliente
                  ? "bg-primary text-white"
                  : "bg-surface border border-border-dark text-slate-400 hover:border-white/10"
              }`}
            >
              Todas
            </button>
            {clientes.map((cliente) => (
              <button
                key={cliente}
                onClick={() => setFiltroCliente(filtroCliente === cliente ? "" : cliente)}
                className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  filtroCliente === cliente
                    ? "bg-primary text-white"
                    : "bg-surface border border-border-dark text-slate-400 hover:border-white/10"
                }`}
              >
                {cliente}
                <span className="ml-1 opacity-60">
                  ({lista.filter((c) => c.cliente === cliente).length})
                </span>
              </button>
            ))}
          </div>
        )}

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

        {/* Lista agrupada por incorporadora */}
        {!loading && Object.entries(agrupadas).map(([cliente, camps]) => (
          <div key={cliente} className="space-y-2">
            {/* Header da incorporadora (só mostra se não está filtrado) */}
            {!filtroCliente && clientes.length > 1 && (
              <div className="flex items-center gap-2 pt-3 pb-1">
                <span className="material-symbols-outlined text-primary" style={{ fontSize: 16 }}>domain</span>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">{cliente}</h3>
                <span className="text-[10px] text-slate-600">({camps.length})</span>
                <div className="flex-1 h-px bg-border-dark ml-2" />
              </div>
            )}

            {/* Cards das campanhas */}
            {camps.map((c) => (
              <div
                key={c.id}
                onClick={() => router.push(`/campanha/${c.id}`)}
                className="w-full bg-card-dark border border-border-dark rounded-2xl p-4 text-left hover:border-white/10 transition-all group cursor-pointer"
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
                        {c.empreendimento || c.cliente}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${statusColor[c.status] || statusColor.rascunho}`}>
                        {c.status}
                      </span>
                      {!filtroCliente && clientes.length <= 1 && (
                        <span className="text-[10px] text-slate-600">{c.cliente}</span>
                      )}
                      <span className="text-[10px] text-slate-600">
                        {new Date(c.criada_em).toLocaleDateString("pt-BR")}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/campanha/${c.id}`);
                      }}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
                      title="Editar campanha"
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>edit</span>
                    </button>
                    <button
                      onClick={(e) => handleDeletar(c.id, e)}
                      disabled={deletando === c.id}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-50"
                      title="Deletar campanha"
                    >
                      <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                        {deletando === c.id ? "hourglass_top" : "delete"}
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </AppShell>
  );
}
