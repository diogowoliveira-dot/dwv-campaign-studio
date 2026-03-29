"use client";
import { useState } from "react";
import { Executivo, ExecutivoInput } from "@/lib/api";

interface Props {
  executivo: Executivo | null;
  onSalvar: (data: ExecutivoInput) => Promise<void>;
  onFechar: () => void;
}

export default function ExecutivoForm({ executivo, onSalvar, onFechar }: Props) {
  const [form, setForm] = useState<ExecutivoInput>({
    nome: executivo?.nome || "",
    cargo: executivo?.cargo || "Executivo de Parcerias",
    regiao: executivo?.regiao || "",
    whatsapp: executivo?.whatsapp || "",
    email: executivo?.email || "",
  });
  const [salvando, setSalvando] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSalvando(true);
    try {
      await onSalvar(form);
    } finally {
      setSalvando(false);
    }
  };

  const campos: { key: keyof ExecutivoInput; label: string; type?: string; placeholder: string }[] = [
    { key: "nome", label: "Nome completo", placeholder: "João Silva" },
    { key: "cargo", label: "Cargo", placeholder: "Executivo de Parcerias" },
    { key: "regiao", label: "Região", placeholder: "Itapema/SC" },
    { key: "whatsapp", label: "WhatsApp", type: "tel", placeholder: "(47) 99999-0000" },
    { key: "email", label: "E-mail", type: "email", placeholder: "joao@dwv.com.br" },
  ];

  return (
    <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-end sm:items-center justify-center">
      <div className="w-full max-w-md bg-card-dark border border-border-dark rounded-t-3xl sm:rounded-3xl p-6 animate-slide-up">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">
            {executivo ? "Editar executivo" : "Novo executivo"}
          </h2>
          <button
            onClick={onFechar}
            className="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>close</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {campos.map((c) => (
            <div key={c.key}>
              <label className="text-xs font-medium text-slate-400 mb-1.5 block">{c.label}</label>
              <input
                type={c.type || "text"}
                value={form[c.key]}
                onChange={(e) => setForm({ ...form, [c.key]: e.target.value })}
                placeholder={c.placeholder}
                required={c.key === "nome"}
                className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
              />
            </div>
          ))}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onFechar}
              className="flex-1 py-3 bg-surface border border-border-dark text-white text-sm font-medium rounded-xl hover:bg-surface-light transition-all"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={salvando}
              className="flex-1 py-3 bg-primary hover:bg-primary-dark text-white text-sm font-semibold rounded-xl transition-all disabled:opacity-50 shadow-glow"
            >
              {salvando ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
