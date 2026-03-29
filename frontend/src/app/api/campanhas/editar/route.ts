import { NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";

const EXEMPLOS_EDICAO = `
Exemplos de interpretação:
- "Aumenta a logo do empreendimento" → Encontrar img da logo e aumentar height em ~30%
- "Muda o CTA para vermelho" → Encontrar .cta ou button e alterar background-color
- "O nome do executivo está pequeno" → Aumentar font-size do .exec-name
- "Troca o headline" → Substituir texto do .headline
- "Aumenta a foto do executivo" → Aumentar width/height da .exec-foto
- "Muda a paleta para azul" → Atualizar cores CSS
- "Remove o subtítulo" → Aplicar display:none no .subtitle
- "Centraliza o bloco do executivo" → Alterar justify-content ou text-align
- "Coleta a logo do site X" → Insira a tag ASSET_LOGO_1 onde a logo deve ficar
- "Usa imagem de fachada" → Insira a tag ASSET_HERO onde a imagem deve ficar
`;

// Fetch a URL and return base64 data URI
async function fetchAsBase64(url: string): Promise<string | null> {
  try {
    const res = await fetch(url, {
      headers: { "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" },
      redirect: "follow",
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    const contentType = res.headers.get("content-type") || "image/png";
    if (!contentType.startsWith("image/")) return null;
    const buffer = await res.arrayBuffer();
    if (buffer.byteLength < 100) return null;
    const base64 = Buffer.from(buffer).toString("base64");
    return `data:${contentType};base64,${base64}`;
  } catch {
    return null;
  }
}

// Extract image URLs from an HTML page
function extractImageUrls(html: string, baseUrl: string): { logos: string[]; images: string[]; ogImage: string } {
  const logos: string[] = [];
  const images: string[] = [];
  let ogImage = "";

  const resolve = (src: string) => {
    if (!src || src.startsWith("data:")) return "";
    try {
      if (src.startsWith("//")) return "https:" + src;
      if (src.startsWith("http")) return src;
      return new URL(src, baseUrl).href;
    } catch { return ""; }
  };

  // Find logos
  const imgRegex = /<img\s+([^>]*?)>/gi;
  let match;
  while ((match = imgRegex.exec(html)) !== null) {
    const attrs = match[1];
    const srcMatch = attrs.match(/(?:src|data-src)\s*=\s*["']([^"']+)["']/i);
    if (!srcMatch) continue;
    const src = resolve(srcMatch[1]);
    if (!src) continue;

    if (/logo|brand|marca/i.test(attrs)) {
      logos.push(src);
    } else {
      images.push(src);
    }
  }

  // og:image
  const ogMatch = html.match(/<meta\s+[^>]*property\s*=\s*["']og:image["'][^>]*content\s*=\s*["']([^"']+)["']/i)
    || html.match(/<meta\s+[^>]*content\s*=\s*["']([^"']+)["'][^>]*property\s*=\s*["']og:image["']/i);
  if (ogMatch) ogImage = resolve(ogMatch[1]);

  // favicon fallback
  const iconMatch = html.match(/<link\s+[^>]*rel\s*=\s*["'][^"]*icon[^"]*["'][^>]*href\s*=\s*["']([^"']+)["']/i);
  if (iconMatch && logos.length === 0) logos.push(resolve(iconMatch[1]));

  return { logos, images, ogImage };
}

function extractUrlsFromMessage(msg: string): string[] {
  const urlRegex = /(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+)(?:\/[^\s,)]*)?/gi;
  const matches = msg.match(urlRegex) || [];
  return matches.map(u => u.startsWith("http") ? u : `https://${u}`);
}

function needsAssetFetch(msg: string): boolean {
  const keywords = ["logo", "fachada", "imagem", "foto", "site", "coleta", "colet", "busca", "busque",
    "pega", "pegue", "usa ", "use ", "utilize", "incorporadora", "empreendimento", "url"];
  const lower = msg.toLowerCase();
  return keywords.some(k => lower.includes(k)) && extractUrlsFromMessage(msg).length > 0;
}

export async function POST(req: Request) {
  try {
    const { mensagem, formato, html_atual, versao_atual } = await req.json();

    if (!mensagem || !html_atual) {
      return NextResponse.json({ detail: "Mensagem e HTML obrigatórios" }, { status: 400 });
    }

    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      return NextResponse.json({
        peca: null,
        mensagem_assistente: `Entendi: "${mensagem}". A API do Claude não está configurada. Adicione ANTHROPIC_API_KEY nas variáveis de ambiente.`,
      });
    }

    const client = new Anthropic({ apiKey });

    // Phase 1: Fetch assets if user mentions a URL
    const fetchedAssets: Record<string, string> = {};
    let assetsSummary = "";

    if (needsAssetFetch(mensagem)) {
      const urls = extractUrlsFromMessage(mensagem);

      for (const url of urls) {
        try {
          const pageRes = await fetch(url, {
            headers: { "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" },
            redirect: "follow",
            signal: AbortSignal.timeout(10000),
          });
          const pageHtml = await pageRes.text();
          const { logos, images, ogImage } = extractImageUrls(pageHtml, url);

          // Fetch first logo
          for (const logoUrl of logos.slice(0, 3)) {
            const b64 = await fetchAsBase64(logoUrl);
            if (b64 && b64.length > 200) {
              if (!fetchedAssets["ASSET_LOGO_1"]) fetchedAssets["ASSET_LOGO_1"] = b64;
              else if (!fetchedAssets["ASSET_LOGO_2"]) fetchedAssets["ASSET_LOGO_2"] = b64;
              break;
            }
          }

          // Fetch hero/fachada image (OG or first large image)
          const heroUrl = ogImage || images.find(u => /fachada|hero|banner|building/i.test(u)) || images[0];
          if (heroUrl && !fetchedAssets["ASSET_HERO"]) {
            const b64 = await fetchAsBase64(heroUrl);
            if (b64 && b64.length > 1000) {
              fetchedAssets["ASSET_HERO"] = b64;
            }
          }
        } catch {
          // continue
        }
      }

      const labels = Object.keys(fetchedAssets);
      if (labels.length > 0) {
        assetsSummary = ` Coletei ${labels.length} asset(s): ${labels.join(", ")}.`;
      } else {
        assetsSummary = " Não consegui encontrar imagens nesse site.";
      }
    }

    // Phase 2: Ask Claude to modify HTML using PLACEHOLDER tags
    const placeholderInstructions = Object.keys(fetchedAssets).length > 0
      ? `\n\nASSETS DISPONÍVEIS — use estes PLACEHOLDERS no HTML onde as imagens devem aparecer:
${Object.keys(fetchedAssets).map(k => `- ${k}: placeholder para ${k.includes("LOGO") ? "logo (use height:44-140px, object-fit:contain)" : "imagem principal/fachada (use como background ou img grande no topo)"}`).join("\n")}

Para cada asset, insira: <img src="${"{{"}${Object.keys(fetchedAssets)[0]}${"}}"}" ...>
Eu vou substituir os placeholders pelos dados reais depois.`
      : "";

    const response = await client.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 8000,
      messages: [
        {
          role: "user",
          content: `Você é um editor de HTML para peças de marketing imobiliário.
Receba o HTML abaixo e aplique a seguinte alteração: ${mensagem}

${EXEMPLOS_EDICAO}

Regras:
- Retorne APENAS o HTML modificado, sem explicações nem markdown
- Mantenha todas as dimensões (width/height do body) e estrutura geral
- Preserve todas as imagens base64 já existentes no HTML
- Aplique apenas o que foi pedido, não mude o resto
- Para assets novos: use src="{{ASSET_LOGO_1}}", src="{{ASSET_LOGO_2}}", ou src="{{ASSET_HERO}}" como placeholder
${placeholderInstructions}

HTML atual:
${html_atual}`,
        },
      ],
    });

    let html_editado = (response.content[0] as { type: string; text: string }).text.trim();

    // Clean code blocks
    if (html_editado.startsWith("```")) {
      html_editado = html_editado.split("\n").slice(1).join("\n");
    }
    if (html_editado.endsWith("```")) {
      html_editado = html_editado.slice(0, html_editado.lastIndexOf("```"));
    }

    // Phase 3: Replace placeholders with real base64 data
    for (const [placeholder, b64] of Object.entries(fetchedAssets)) {
      html_editado = html_editado.replaceAll(`{{${placeholder}}}`, b64);
    }

    return NextResponse.json({
      peca: {
        id: `peca-${Date.now()}`,
        formato,
        versao: (versao_atual || 1) + 1,
        html: html_editado,
        arquivo_url: "",
      },
      mensagem_assistente: `Pronto! Apliquei: "${mensagem}".${assetsSummary}`,
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Erro desconhecido";
    return NextResponse.json(
      { detail: `Erro ao editar: ${message}` },
      { status: 500 },
    );
  }
}
