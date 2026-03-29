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

  const handleEditar = async (texto: string) => {
    // Adiciona mensagem do usuario localmente
    const userMsg: Mensagem = {
      id: `temp-${Date.now()}`,
      role: "user",
      conteudo: texto,
      criada_em: new Date().toISOString(),
    };
    setMensagens((prev) => [...prev, userMsg]);

    // Pega o HTML atual da peça sendo editada para enviar ao Claude
    const pecaAtual = campanha?.pecas.find((p) => p.formato === formato);
    const response = await campanhas.editar(id, texto, formato, pecaAtual?.html, pecaAtual?.versao);

    // Adiciona resposta do assistente
    const assistantMsg: Mensagem = {
      id: `temp-${Date.now()}-resp`,
      role: "assistant",
      conteudo: response.mensagem_assistente,
      criada_em: new Date().toISOString(),
    };
    setMensagens((prev) => [...prev, assistantMsg]);

    // Atualiza peca (só se o backend retornou uma peça válida)
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
    >
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
            pecas={campanha.pecas}
            onFormatoChange={setFormato}
          />
        </div>
      </div>
    </AppShell>
  );
}
