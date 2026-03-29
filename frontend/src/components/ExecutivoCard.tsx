"use client";
import { Executivo } from "@/lib/api";
import { useRef } from "react";

interface Props {
  executivo: Executivo;
  onEdit: () => void;
  onToggle: () => void;
  onFoto: (file: File) => void;
}

export default function ExecutivoCard({ executivo, onEdit, onToggle, onFoto }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <div className={`bg-card-dark border border-border-dark rounded-2xl p-4 transition-all ${!executivo.ativo ? "opacity-50" : ""}`}>
      <div className="flex items-center gap-3">
        {/* Foto */}
        <button
          onClick={() => fileRef.current?.click()}
          className="relative w-12 h-12 rounded-xl bg-surface flex-shrink-0 overflow-hidden group"
        >
          {executivo.foto_url ? (
            <img src={executivo.foto_url} alt={executivo.nome} className="w-full h-full object-cover" />
          ) : (
            <span className="material-symbols-outlined text-slate-600 absolute inset-0 flex items-center justify-center" style={{ fontSize: 24 }}>
              person
            </span>
          )}
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <span className="material-symbols-outlined text-white" style={{ fontSize: 16 }}>
              photo_camera
            </span>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) onFoto(file);
            }}
          />
        </button>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold truncate">{executivo.nome}</h3>
          <p className="text-[11px] text-slate-500 truncate">{executivo.cargo}</p>
          <div className="flex items-center gap-2 mt-1">
            {executivo.regiao && (
              <span className="text-[10px] text-slate-600 flex items-center gap-0.5">
                <span className="material-symbols-outlined" style={{ fontSize: 12 }}>location_on</span>
                {executivo.regiao}
              </span>
            )}
            {executivo.whatsapp && (
              <span className="text-[10px] text-slate-600 flex items-center gap-0.5">
                <span className="material-symbols-outlined" style={{ fontSize: 12 }}>phone</span>
                {executivo.whatsapp}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={onEdit}
            className="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>edit</span>
          </button>
          <button
            onClick={onToggle}
            className={`p-2 rounded-lg transition-all ${
              executivo.ativo
                ? "text-success hover:bg-success/10"
                : "text-slate-600 hover:bg-white/5"
            }`}
          >
            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
              {executivo.ativo ? "toggle_on" : "toggle_off"}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
