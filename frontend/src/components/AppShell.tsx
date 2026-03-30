"use client";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { useEffect, ReactNode } from "react";
import BottomNav from "./BottomNav";

interface AppShellProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
  icon?: string;
  showBack?: boolean;
  actions?: ReactNode;
  hideNav?: boolean;
}

export default function AppShell({
  children,
  title,
  subtitle,
  icon,
  showBack = false,
  actions,
  hideNav = false,
}: AppShellProps) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/");
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <div className="bg-black text-white min-h-screen pb-28">
      <header className="sticky top-0 z-50 bg-black/90 backdrop-blur-xl border-b border-white/[0.06]">
        <div className="flex items-center justify-between px-5 py-4 max-w-5xl mx-auto">
          <div className="flex items-center gap-3 min-w-0">
            {showBack && (
              <button
                onClick={() => router.push("/dashboard")}
                className="p-1 -ml-1 text-slate-400 hover:text-white transition-colors"
              >
                <span className="material-symbols-outlined" style={{ fontSize: 22 }}>
                  arrow_back
                </span>
              </button>
            )}
            {icon && (
              <span className="material-symbols-outlined text-primary" style={{ fontSize: 22 }}>
                {icon}
              </span>
            )}
            <div className="min-w-0">
              <h1 className="text-base font-bold tracking-tight truncate">{title}</h1>
              {subtitle && (
                <p className="text-[11px] text-slate-500 truncate">{subtitle}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1">
            {actions}
            <button
              onClick={() => router.push("/dashboard")}
              className="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
              title="Início"
            >
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>home</span>
            </button>
            <button
              onClick={() => { logout(); router.push("/"); }}
              className="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
              title="Sair"
            >
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>logout</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto">{children}</main>

      {!hideNav && <BottomNav />}
    </div>
  );
}
