"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useTransition } from "react";
import { QUESTION_IDS, RESEARCH_QUESTIONS } from "@/lib/types";

const NAV = [
  { href: "/", label: "Home", icon: "dashboard" },
  { href: "/pm-buddy", label: "PM Buddy", icon: "psychology" },
  { href: "/trends", label: "Trends", icon: "trending_up" },
  { href: "/runs", label: "History", icon: "history" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    for (const item of NAV) router.prefetch(item.href);
    for (const id of QUESTION_IDS) router.prefetch(`/questions/${id}`);
    router.prefetch("/trends");
    router.prefetch("/runs");
    router.prefetch("/pm-buddy");
  }, [router]);

  function navigate(href: string) {
    if (pathname === href) return;
    startTransition(() => {
      router.push(href);
    });
  }

  return (
    <aside className="hidden md:flex flex-col py-8 gap-y-4 bg-surface-container-lowest h-screen w-64 fixed left-0 top-0 border-r border-border-subtle z-40">
      <div className="px-6 mb-8 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-surface-high flex items-center justify-center border border-border-subtle overflow-hidden relative">
          <div
            className="absolute inset-0 bg-cover bg-center opacity-50 mix-blend-screen"
            style={{
              backgroundImage:
                "url('https://lh3.googleusercontent.com/aida-public/AB6AXuBqGeOLuHedoMJMXwRr6DMtneOcnGZRkkPHN3WC9Q50brhJyHeZjoLH7bGLiia4ji1t-ercC8boTZ0r3MaiPbHw8yI1WZvqeEQBoJa9D6D_TAuDuZKd2uqE38CYLDHBWcGpYzfIBl85H63d0jTZs-Aryrd0ZPUx8rK8qXwLJTfyERA40u88cIl_uVxc4tpLQKz1JgqAE3P31Jx9FrAgM6Bcb0bMau0eg8t_jXUZX5sYa-I3biYs8OMFtHqn2vWNHTH5qbDt2Ww4b4mJ')",
            }}
          ></div>
          <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>
            graphic_eq
          </span>
        </div>
        <div>
          <h1 className="text-[20px] font-semibold text-primary leading-tight">
            Discovery Engine
          </h1>
        </div>
      </div>

      <nav className="flex-1 px-2 space-y-1 mt-2">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <button
              key={item.href}
              type="button"
              onClick={() => navigate(item.href)}
              className={`w-full flex items-center gap-3 py-2 px-4 rounded-lg transition-colors ${
                active
                  ? "text-primary font-bold border-l-2 border-primary bg-primary/5 translate-x-1"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high pl-4"
              } ${isPending && !active ? "opacity-80" : ""}`}
            >
              <span className="material-symbols-outlined text-[20px]">
                {item.icon}
              </span>
              <span className="text-[12px] font-semibold uppercase tracking-wider">
                {item.label}
              </span>
            </button>
          );
        })}

        <div className="pt-4 mt-4 border-t border-border-subtle">
          <p className="px-4 text-[11px] uppercase tracking-wider text-text-muted mb-2">
            Questions
          </p>
          {QUESTION_IDS.map((id) => {
            const href = `/questions/${id}`;
            const active = pathname === href;
            const meta = RESEARCH_QUESTIONS[id];
            return (
              <button
                key={id}
                type="button"
                onClick={() => navigate(href)}
                className={`w-full flex items-center gap-2 py-1.5 px-4 rounded-lg text-[13px] transition-colors ${
                  active
                    ? "text-primary bg-primary/5"
                    : "text-text-muted hover:text-on-surface hover:bg-surface-container-high"
                } ${isPending && !active ? "opacity-80" : ""}`}
              >
                <span className="font-semibold">Q{meta.order}</span>
                <span className="truncate text-left">{meta.short}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </aside>
  );
}
