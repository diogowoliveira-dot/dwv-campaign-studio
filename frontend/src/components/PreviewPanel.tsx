"use client";
import { useState, useEffect } from "react";
import { Peca, campanhas } from "@/lib/api";

interface Props {
  campanhaId: string;
  pecas: Peca[];
  onFormatoChange?: (formato: string) => void;
}

const tabs = [
  { key: "story", label: "Story", icon: "phone_android", w: 1080, h: 1920 },
  { key: "post", label: "Post", icon: "crop_square", w: 1080, h: 1080 },
  { key: "email", label: "E-mail", icon: "email", w: 600, h: 900 },
];

function downloadHtml(html: string, formato: string, versao: number) {
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${formato}_v${versao}.html`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function PreviewPanel({ campanhaId, pecas, onFormatoChange }: Props) {
  const [aba, setAba] = useState("story");
  const [htmlCache, setHtmlCache] = useState<Record<string, string>>({});
  const [loadingHtml, setLoadingHtml] = useState(false);

  const pecaAtual = pecas.find((p) => p.formato === aba);
  const tab = tabs.find((t) => t.key === aba)!;
  const htmlAtual = pecaAtual ? (htmlCache[pecaAtual.id] || pecaAtual.html || "") : "";

  // Load HTML on demand when tab changes
  useEffect(() => {
    if (!pecaAtual) return;
    // Already have HTML in cache or in peca object
    if (htmlCache[pecaAtual.id] || pecaAtual.html) return;

    setLoadingHtml(true);
    campanhas.obterPeca(campanhaId, aba)
      .then((peca) => {
        if (peca?.html) {
          setHtmlCache((prev) => ({ ...prev, [pecaAtual.id]: peca.html }));
        }
      })
      .catch(() => {})
      .finally(() => setLoadingHtml(false));
  }, [aba, pecaAtual, campanhaId]);

  const handleTab = (key: string) => {
    setAba(key);
    onFormatoChange?.(key);
  };

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

        {/* Downloads */}
        {pecaAtual && htmlAtual && (
          <div className="ml-auto flex items-center gap-1 mr-3">
            <button
              onClick={() => downloadHtml(htmlAtual, pecaAtual.formato, pecaAtual.versao)}
              className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
              title="Baixar HTML"
            >
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>download</span>
            </button>
          </div>
        )}
      </div>

      {/* Preview */}
      <div className="flex-1 overflow-auto p-4 flex items-start justify-center">
        {loadingHtml ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-xs text-slate-500">Carregando {tab.label}...</p>
          </div>
        ) : pecaAtual && htmlAtual ? (
          <div>
            <div
              className="rounded-xl overflow-hidden border border-border-dark"
              style={{ width: containerWidth, height: scaledHeight }}
            >
              <iframe
                srcDoc={htmlAtual}
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
            <p className="text-center text-[10px] text-slate-600 mt-2">
              Versão {pecaAtual.versao} — {tab.label} — {tab.w}×{tab.h}
            </p>
          </div>
        ) : pecaAtual ? (
          <div className="text-center py-20">
            <span className="material-symbols-outlined text-slate-700 mb-2 block" style={{ fontSize: 40 }}>image</span>
            <p className="text-sm text-slate-500">Peça sem conteúdo</p>
          </div>
        ) : (
          <div className="text-center py-20">
            <span className="material-symbols-outlined text-slate-700 mb-2 block" style={{ fontSize: 40 }}>image</span>
            <p className="text-sm text-slate-500">Nenhuma peça gerada</p>
            <p className="text-xs text-slate-600 mt-1">A peça aparecerá aqui após a geração</p>
          </div>
        )}
      </div>
    </div>
  );
}
