"use client";
import { useState, useEffect } from "react";
import AppShell from "@/components/AppShell";
import ExecutivoCard from "@/components/ExecutivoCard";
import ExecutivoForm from "@/components/ExecutivoForm";
import { executivos as api, Executivo, ExecutivoInput } from "@/lib/api";

export default function ExecutivosPage() {
  const [lista, setLista] = useState<Executivo[]>([]);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<Executivo | null>(null);

  const carregar = () => {
    setLoading(true);
    api.listar()
      .then(setLista)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(carregar, []);

  const filtrados = lista.filter(
    (e) =>
      e.nome.toLowerCase().includes(busca.toLowerCase()) ||
      e.regiao.toLowerCase().includes(busca.toLowerCase())
  );

  const handleSalvar = async (data: ExecutivoInput) => {
    if (editando) {
      await api.atualizar(editando.id, data);
    } else {
      await api.criar(data);
    }
    setShowForm(false);
    setEditando(null);
    carregar();
  };

  const handleToggle = async (exec: Executivo) => {
    await api.toggle(exec.id);
    carregar();
  };

  const handleEditar = (exec: Executivo) => {
    setEditando(exec);
    setShowForm(true);
  };

  const handleFoto = async (exec: Executivo, file: File) => {
    await api.uploadFoto(exec.id, file);
    carregar();
  };

  return (
    <AppShell
      title="Executivos"
      subtitle="Gestão de perfis"
      icon="group"
      actions={
        <button
          onClick={() => { setEditando(null); setShowForm(true); }}
          className="p-2 rounded-lg text-primary hover:bg-primary/10 transition-all"
        >
          <span className="material-symbols-outlined" style={{ fontSize: 20 }}>person_add</span>
        </button>
      }
    >
      <div className="px-5 py-6 space-y-4">
        {/* Busca */}
        <div className="relative">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" style={{ fontSize: 20 }}>
            search
          </span>
          <input
            type="text"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar por nome ou região..."
            className="w-full pl-10 pr-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 transition-all"
          />
        </div>

        {/* Contador */}
        <p className="text-xs text-slate-500">
          {filtrados.length} executivo{filtrados.length !== 1 ? "s" : ""}
          {busca && ` encontrado${filtrados.length !== 1 ? "s" : ""}`}
        </p>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Lista */}
        {!loading && filtrados.length === 0 && (
          <div className="text-center py-20">
            <span className="material-symbols-outlined text-slate-700 mb-3 block" style={{ fontSize: 48 }}>
              group
            </span>
            <p className="text-slate-500 text-sm">
              {busca ? "Nenhum executivo encontrado" : "Nenhum executivo cadastrado"}
            </p>
          </div>
        )}

        <div className="space-y-3">
          {filtrados.map((exec) => (
            <ExecutivoCard
              key={exec.id}
              executivo={exec}
              onEdit={() => handleEditar(exec)}
              onToggle={() => handleToggle(exec)}
              onFoto={(file) => handleFoto(exec, file)}
            />
          ))}
        </div>
      </div>

      {/* Modal Form */}
      {showForm && (
        <ExecutivoForm
          executivo={editando}
          onSalvar={handleSalvar}
          onFechar={() => { setShowForm(false); setEditando(null); }}
        />
      )}
    </AppShell>
  );
}
