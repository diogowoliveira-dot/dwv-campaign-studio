"use client";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import BriefingForm from "@/components/BriefingForm";
import { campanhas, CampanhaInput } from "@/lib/api";

export default function NovaCampanhaPage() {
  const router = useRouter();

  const handleSubmit = async (data: CampanhaInput) => {
    const campanha = await campanhas.criar(data);
    await campanhas.gerar(campanha.id);
    router.push(`/campanha/${campanha.id}`);
  };

  return (
    <AppShell title="Nova campanha" subtitle="Preencha o briefing" icon="add_circle" showBack>
      <div className="px-5 py-6">
        <BriefingForm onSubmit={handleSubmit} />
      </div>
    </AppShell>
  );
}
