"use client";
import { usePathname, useRouter } from "next/navigation";

const items = [
  { label: "Campanhas", icon: "campaign", path: "/dashboard" },
  { label: "Nova", icon: "add_circle", path: "/campanha/nova" },
  { label: "Executivos", icon: "group", path: "/executivos" },
];

export default function BottomNav() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-black/95 backdrop-blur-xl border-t border-white/[0.06]">
      <div className="flex items-center justify-around max-w-5xl mx-auto py-2">
        {items.map((item) => {
          const active = pathname.startsWith(item.path);
          return (
            <button
              key={item.path}
              onClick={() => router.push(item.path)}
              className={`flex flex-col items-center gap-0.5 px-4 py-1.5 rounded-xl transition-all ${
                active ? "text-primary" : "text-slate-500 hover:text-slate-300"
              }`}
            >
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 22, fontVariationSettings: active ? "'FILL' 1" : "'FILL' 0" }}
              >
                {item.icon}
              </span>
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
