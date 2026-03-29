import { NextResponse } from "next/server";

// Demo auth — aceita qualquer email/senha
export async function POST(req: Request) {
  const { email, senha } = await req.json();

  if (!email || !senha) {
    return NextResponse.json({ detail: "E-mail e senha obrigatórios" }, { status: 400 });
  }

  return NextResponse.json({
    user: { id: "user-1", email, nome: email.split("@")[0] },
    token: "demo-token-" + Date.now(),
  });
}
