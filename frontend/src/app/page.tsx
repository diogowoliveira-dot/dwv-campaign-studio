"use client";
import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function LoginPage() {
  const { user, login, loading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (user) router.push("/dashboard");
    // Pre-warm backend while user sees login screen
    if (process.env.NEXT_PUBLIC_API_URL) {
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/`, { mode: "no-cors" }).catch(() => {});
    }
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro("");
    setEnviando(true);
    try {
      await login(email, senha);
      router.push("/dashboard");
    } catch {
      setErro("E-mail ou senha incorretos");
    } finally {
      setEnviando(false);
    }
  };

  if (loading) return null;
  if (user) return null;

  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-6">
      <div className="w-full max-w-sm animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <span className="material-symbols-outlined text-white" style={{ fontSize: 24 }}>
                campaign
              </span>
            </div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Estúdio de Campanhas</h1>
          <p className="text-sm text-slate-500 mt-1">DWV — Gestão de Parcerias</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">E-mail</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              required
              className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Senha</label>
            <input
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full px-4 py-3 bg-surface border border-border-dark rounded-xl text-white text-sm placeholder:text-slate-600 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
            />
          </div>

          {erro && (
            <p className="text-xs text-danger text-center">{erro}</p>
          )}

          <button
            type="submit"
            disabled={enviando}
            className="w-full py-3 bg-primary hover:bg-primary-dark text-white font-semibold text-sm rounded-xl transition-all disabled:opacity-50 shadow-glow"
          >
            {enviando ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="text-center text-[11px] text-slate-600 mt-8">
          DWV Estúdio de Campanhas v1.0
        </p>
      </div>
    </div>
  );
}
