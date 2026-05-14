"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, CalendarDays, LayoutGrid, GitBranchPlus, Trophy } from "lucide-react";
import { cn } from "../lib/cn";

const items = [
  { href: "/", label: "Home", icon: LayoutDashboard },
  { href: "/groups", label: "Groups", icon: LayoutGrid },
  { href: "/fixtures", label: "Fixtures", icon: CalendarDays },
  { href: "/bracket", label: "Bracket", icon: GitBranchPlus },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <div className="sticky top-0 z-30 border-b border-line/70 bg-bg/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
        <Link href="/" className="group inline-flex items-center gap-2.5">
          <span className="relative inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-cup shadow-glow">
            <Trophy className="h-4 w-4 text-black" aria-hidden />
          </span>
          <div className="leading-tight">
            <div className="text-sm font-extrabold tracking-tight">WC26 Predictor</div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-muted">
              FIFA World Cup 2026 forecasts
            </div>
          </div>
        </Link>
        <nav aria-label="Primary" className="scrollbar-thin -mx-1 flex max-w-full items-center gap-1 overflow-x-auto px-1">
          {items.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname?.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "inline-flex h-9 shrink-0 items-center gap-1.5 rounded-xl border px-3 text-sm font-medium transition-colors duration-200",
                  active
                    ? "border-gold-500/40 bg-gold-500/10 text-ink"
                    : "border-transparent text-muted hover:border-line/80 hover:bg-surface2 hover:text-ink"
                )}
              >
                <Icon className="h-4 w-4" aria-hidden />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
