"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import BriefingForm from "@/components/BriefingForm";
import { campanhas, CampanhaInput } from "@/lib/api";

export default function NovaCampanhaPage() {
  const router = useRouter();
  const [erro, setErro] = useState("");

  const handleSubmit = async (data: CampanhaInput) => {
    setErro("");
    try {
      const campanha = await campanhas.criar(data);
      try {
        await campanhas.gerar(campanha.id);
      } catch (genErr) {
        // Geração falhou mas campanha foi criada — redireciona mesmo assim
        console.warn("Geração falhou:", genErr);
      }
      router.push(`/campanha/${campanha.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro desconhecido";
      setErro(msg);
    }
  };

  return (
    <AppShell title="Nova campanha" subtitle="Preencha o briefing" icon="add_circle" showBack>
      <div className="px-5 py-6">
        {erro && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
            {erro}
          </div>
        )}
        <BriefingForm onSubmit={handleSubmit} />
      </div>
    </AppShell>
  );
}
