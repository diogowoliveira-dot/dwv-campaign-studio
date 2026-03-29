"use client";
import { useState } from "react";
import { Peca } from "@/lib/api";

interface Props {
  pecas: Peca[];
  onFormatoChange?: (formato: string) => void;
}

const tabs = [
  { key: "story", label: "Story", icon: "phone_android", w: 1080, h: 1920 },
  { key: "post", label: "Post", icon: "crop_square", w: 1080, h: 1080 },
  { key: "email", label: "E-mail", icon: "email", w: 600, h: 900 },
];

export default function PreviewPanel({ pecas, onFormatoChange }: Props) {
  const [aba, setAba] = useState("story");

  const pecaAtual = pecas.find((p) => p.formato === aba);
  const tab = tabs.find((t) => t.key === aba)!;

  const handleTab = (key: string) => {
    setAba(key);
    onFormatoChange?.(key);
  };

  // Escala para caber no container (~360px de largura)
  const containerWidth = 360;
  const scale = containerWidth / tab.w;
  const scaledHeight = tab.h * scale;

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex items-center border-b border-border-dark">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => handleTab(t.key)}
            className={`flex items-center gap-1.5 px-4 py-3 text-xs font-medium transition-all border-b-2 ${
              aba === t.key
                ? "border-primary text-primary"
                : "border-transparent text-slate-500 hover:text-slate-300"
            }`}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{t.icon}</span>
            {t.label}
          </button>
        ))}

        {/* Download */}
        {pecaAtual?.arquivo_url && (
          <a
            href={pecaAtual.arquivo_url}
            download
            className="ml-auto mr-3 p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>download</span>
          </a>
        )}
      </div>

      {/* Preview */}
      <div className="flex-1 overflow-auto p-4 flex items-start justify-center">
        {pecaAtual ? (
          <div>
            {pecaAtual.arquivo_url && aba !== "email" ? (
              <img
                src={pecaAtual.arquivo_url}
                alt={`Preview ${tab.label}`}
                className="rounded-xl border border-border-dark"
                style={{ width: containerWidth }}
              />
            ) : (
              <div
                className="rounded-xl overflow-hidden border border-border-dark"
                style={{ width: containerWidth, height: scaledHeight }}
              >
                <iframe
                  srcDoc={pecaAtual.html}
                  className="border-0"
                  style={{
                    width: tab.w,
                    height: tab.h,
                    transform: `scale(${scale})`,
                    transformOrigin: "top left",
                  }}
                  sandbox="allow-same-origin"
                />
              </div>
            )}
            <p className="text-center text-[10px] text-slate-600 mt-2">
              Versao {pecaAtual.versao} — {tab.label}
            </p>
          </div>
        ) : (
          <div className="text-center py-20">
            <span className="material-symbols-outlined text-slate-700 mb-2 block" style={{ fontSize: 40 }}>
              image
            </span>
            <p className="text-sm text-slate-500">Nenhuma peca gerada</p>
            <p className="text-xs text-slate-600 mt-1">A peca aparecera aqui apos a geracao</p>
          </div>
        )}
      </div>
    </div>
  );
}
