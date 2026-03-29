"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface User {
  id: string;
  email: string;
  nome: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, senha: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("dwv_user");
    if (stored) {
      setUser(JSON.parse(stored));
    }
    setLoading(false);
  }, []);

  const login = async (email: string, senha: string) => {
    // Modo demo: qualquer email/senha funciona enquanto o backend não está configurado
    const DEMO_MODE = !process.env.NEXT_PUBLIC_API_URL;

    if (DEMO_MODE) {
      const demoUser = { id: "demo-1", email, nome: email.split("@")[0] };
      setUser(demoUser);
      localStorage.setItem("dwv_user", JSON.stringify(demoUser));
      localStorage.setItem("dwv_token", "demo-token");
      return;
    }

    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    if (!res.ok) throw new Error("Credenciais inválidas");
    const data = await res.json();
    setUser(data.user);
    localStorage.setItem("dwv_user", JSON.stringify(data.user));
    localStorage.setItem("dwv_token", data.token);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("dwv_user");
    localStorage.removeItem("dwv_token");
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return ctx;
}
