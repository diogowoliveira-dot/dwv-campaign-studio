"use client";
import { useState, useRef, useEffect } from "react";
import { Mensagem } from "@/lib/api";

interface Props {
  mensagens: Mensagem[];
  onEnviar: (texto: string) => Promise<void>;
  loading?: boolean;
}

export default function ChatPanel({ mensagens, onEnviar, loading }: Props) {
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [mensagens]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!texto.trim() || enviando) return;
    const msg = texto.trim();
    setTexto("");
    setEnviando(true);
    try {
      await onEnviar(msg);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Mensagens */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-3">
        {mensagens.length === 0 && !loading && (
          <div className="text-center py-10">
            <span className="material-symbols-outlined text-slate-700 mb-2 block" style={{ fontSize: 40 }}>
              chat
            </span>
            <p className="text-sm text-slate-500">Campanha gerada com sucesso!</p>
            <p className="text-xs text-slate-600 mt-1">
              Digite no chat para editar as peças.<br />
              Ex: &ldquo;Aumenta a logo&rdquo; ou &ldquo;Muda o CTA para azul&rdquo;
            </p>
          </div>
        )}

        {mensagens.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-primary text-white rounded-br-md"
                  : "bg-surface border border-border-dark text-slate-200 rounded-bl-md"
              }`}
            >
              {msg.conteudo}
            </div>
          </div>
        ))}

        {(enviando || loading) && (
          <div className="flex justify-start">
            <div className="bg-surface border border-border-dark rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse-dot" />
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse-dot" style={{ animationDelay: "0.2s" }} />
                <div className="w-2 h-2 bg-primary rounded-full animate-pulse-dot" style={{ animationDelay: "0.4s" }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-border-dark">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Peça uma edição..."
            disabled={enviando}
            className="flex-1 px-4 py-2.5 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={enviando || !texto.trim()}
            className="p-2.5 bg-primary hover:bg-primary-dark rounded-xl text-white transition-all disabled:opacity-30"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>send</span>
          </button>
        </div>
      </form>
    </div>
  );
}
