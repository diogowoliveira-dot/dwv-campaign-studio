"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import ChatPanel from "@/components/ChatPanel";
import PreviewPanel from "@/components/PreviewPanel";
import { campanhas, CampanhaCompleta, Mensagem } from "@/lib/api";

export default function CampanhaPage() {
  const params = useParams();
  const id = params.id as string;

  const [campanha, setCampanha] = useState<CampanhaCompleta | null>(null);
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [formato, setFormato] = useState("story");
  const [loading, setLoading] = useState(true);
  const [regerando, setRegerando] = useState(false);

  const carregar = async () => {
    try {
      const data = await campanhas.obter(id);
      setCampanha(data);
      setMensagens(data.mensagens);
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, [id]);

  const handleRegerar = async () => {
    if (!confirm("Regerar todas as peças com os templates atualizados?")) return;
    setRegerando(true);
    try {
      await campanhas.gerar(id);
      await carregar();
    } catch (err) {
      console.warn("Regeração falhou:", err);
    } finally {
      setRegerando(false);
    }
  };

  const handleEditar = async (texto: string) => {
    const userMsg: Mensagem = {
      id: `temp-${Date.now()}`,
      role: "user",
      conteudo: texto,
      criada_em: new Date().toISOString(),
    };
    setMensagens((prev) => [...prev, userMsg]);

    const pecaAtual = campanha?.pecas.find((p) => p.formato === formato);
    const response = await campanhas.editar(id, texto, formato, pecaAtual?.html, pecaAtual?.versao);

    const assistantMsg: Mensagem = {
      id: `temp-${Date.now()}-resp`,
      role: "assistant",
      conteudo: response.mensagem_assistente,
      criada_em: new Date().toISOString(),
    };
    setMensagens((prev) => [...prev, assistantMsg]);

    if (campanha && response.peca?.html) {
      const pecasAtualizadas = campanha.pecas.map((p) =>
        p.formato === formato ? response.peca : p
      );
      setCampanha({ ...campanha, pecas: pecasAtualizadas });
    }
  };

  if (loading) {
    return (
      <AppShell title="Carregando..." icon="campaign" showBack>
        <div className="flex items-center justify-center py-40">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      </AppShell>
    );
  }

  if (!campanha) {
    return (
      <AppShell title="Campanha" icon="campaign" showBack>
        <div className="text-center py-40">
          <p className="text-slate-500">Campanha não encontrada</p>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      title={`${campanha.cliente} — ${campanha.empreendimento}`}
      subtitle={campanha.executivo?.nome}
      icon="campaign"
      showBack
      hideNav
      actions={
        <button
          onClick={handleRegerar}
          disabled={regerando}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-white/5 transition-all disabled:opacity-50"
          title="Regerar peças com templates atualizados"
        >
          <span className={`material-symbols-outlined ${regerando ? "animate-spin" : ""}`} style={{ fontSize: 16 }}>
            {regerando ? "progress_activity" : "refresh"}
          </span>
          {regerando ? "Regerando..." : "Regerar"}
        </button>
      }
    >
      {/* Regerando overlay */}
      {regerando && (
        <div className="fixed inset-0 z-50 bg-black/80 flex flex-col items-center justify-center">
          <div className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full animate-spin mb-6" />
          <p className="text-white font-semibold text-lg">Regerando materiais...</p>
          <p className="text-slate-500 text-sm mt-2">Coletando assets e gerando copy atualizada</p>
        </div>
      )}

      <div className="flex flex-col lg:flex-row" style={{ height: "calc(100vh - 64px)" }}>
        {/* Chat */}
        <div className="lg:w-[400px] lg:border-r border-border-dark flex-shrink-0 h-1/2 lg:h-full">
          <ChatPanel
            mensagens={mensagens}
            onEnviar={handleEditar}
          />
        </div>

        {/* Preview */}
        <div className="flex-1 h-1/2 lg:h-full bg-card-dark/50">
          <PreviewPanel
            campanhaId={id}
            pecas={campanha.pecas}
            onFormatoChange={setFormato}
          />
        </div>
      </div>
    </AppShell>
  );
}
