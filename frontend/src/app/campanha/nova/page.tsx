"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import BriefingForm from "@/components/BriefingForm";
import { campanhas, CampanhaInput } from "@/lib/api";

const LOADING_STEPS = [
  { label: "Coletando assets do site...", icon: "image_search", duration: 3000 },
  { label: "Analisando logos e imagens...", icon: "palette", duration: 2000 },
  { label: "Extraindo conteúdo do empreendimento...", icon: "description", duration: 3000 },
  { label: "Gerando copy com IA...", icon: "auto_awesome", duration: 8000 },
  { label: "Montando Story (1080×1920)...", icon: "phone_android", duration: 3000 },
  { label: "Montando Post (1080×1080)...", icon: "crop_square", duration: 2000 },
  { label: "Montando Email Marketing...", icon: "email", duration: 2000 },
  { label: "Finalizando materiais...", icon: "check_circle", duration: 2000 },
];

export default function NovaCampanhaPage() {
  const router = useRouter();
  const [erro, setErro] = useState("");
  const [gerando, setGerando] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  const handleSubmit = async (data: CampanhaInput) => {
    setErro("");
    setGerando(true);
    setStepIndex(0);

    // Animate through steps
    let currentStep = 0;
    const stepInterval = setInterval(() => {
      currentStep++;
      if (currentStep < LOADING_STEPS.length) {
        setStepIndex(currentStep);
      }
    }, 3000);

    try {
      const campanha = await campanhas.criar(data);
      try {
        await campanhas.gerar(campanha.id);
      } catch (genErr) {
        console.warn("Geração falhou:", genErr);
      }
      clearInterval(stepInterval);
      router.push(`/campanha/${campanha.id}`);
    } catch (err: unknown) {
      clearInterval(stepInterval);
      setGerando(false);
      const msg = err instanceof Error ? err.message : "Erro desconhecido";
      setErro(msg);
    }
  };

  if (gerando) {
    const step = LOADING_STEPS[stepIndex] || LOADING_STEPS[LOADING_STEPS.length - 1];
    return (
      <AppShell title="Gerando campanha" icon="auto_awesome">
        <div className="flex flex-col items-center justify-center min-h-[70vh] px-8">
          {/* Animated ring */}
          <div className="relative w-24 h-24 mb-8">
            <div className="absolute inset-0 border-4 border-primary/20 rounded-full" />
            <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary" style={{ fontSize: 32 }}>
                {step.icon}
              </span>
            </div>
          </div>

          {/* Current step */}
          <p className="text-white font-semibold text-lg mb-2 text-center">{step.label}</p>

          {/* Progress bar */}
          <div className="w-full max-w-xs bg-surface rounded-full h-1.5 mt-4 overflow-hidden">
            <div
              className="bg-primary h-full rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${((stepIndex + 1) / LOADING_STEPS.length) * 100}%` }}
            />
          </div>

          {/* Steps completed */}
          <p className="text-slate-600 text-xs mt-3">
            {stepIndex + 1} de {LOADING_STEPS.length} etapas
          </p>

          {/* Disclaimer */}
          <p className="text-slate-700 text-[10px] mt-8 text-center max-w-xs">
            A IA está analisando o site, coletando imagens e gerando copy profissional para cada formato. Isso pode levar até 30 segundos.
          </p>
        </div>
      </AppShell>
    );
  }

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
