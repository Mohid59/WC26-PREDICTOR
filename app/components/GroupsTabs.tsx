"use client";
import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Crown, Medal, ShieldCheck, ArrowDown } from "lucide-react";
import { MatchCard } from "./MatchCard";
import { TeamLabel } from "./TeamLabel";
import { cn } from "../lib/cn";
import type { Prediction } from "../lib/types";

type GroupFinish = Record<string, Record<string, Record<string, number>>>;

export function GroupsTabs({
  groupKeys,
  groupPredictions,
  groupFinish,
  names,
}: {
  groupKeys: string[];
  groupPredictions: Record<string, Prediction[]>;
  groupFinish: GroupFinish;
  names: Record<string, string>;
}) {
  const [active, setActive] = useState<string>(groupKeys[0] ?? "A");

  const standings = useMemo(() => {
    return Object.fromEntries(
      groupKeys.map((g) => {
        const teams = Object.entries(groupFinish[g] ?? {}).map(([code, posMap]) => {
          const p1 = posMap["1"] ?? 0;
          const p2 = posMap["2"] ?? 0;
          const p3 = posMap["3"] ?? 0;
          const p4 = posMap["4"] ?? 0;
          const advance = p1 + p2 + p3 * 0.4; // rough advance scoring (top-2 + best 3rds)
          const expectedFinish = 1 * p1 + 2 * p2 + 3 * p3 + 4 * p4;
          return { code, p1, p2, p3, p4, advance, expectedFinish };
        });
        teams.sort(
          (a, b) =>
            b.p1 - a.p1 ||
            b.advance - a.advance ||
            a.expectedFinish - b.expectedFinish ||
            a.code.localeCompare(b.code)
        );
        return [g, teams];
      })
    ) as Record<string, Array<{ code: string; p1: number; p2: number; p3: number; p4: number; advance: number; expectedFinish: number }>>;
  }, [groupKeys, groupFinish]);

  return (
    <div className="space-y-5">
      <div role="tablist" aria-label="Groups" className="tabs">
        {groupKeys.map((g) => (
          <button
            key={g}
            role="tab"
            aria-selected={active === g}
            data-state={active === g ? "active" : "inactive"}
            onClick={() => setActive(g)}
            className="tab font-mono"
          >
            <span className="text-xs uppercase tracking-widest text-muted">Group</span>
            <span className="font-bold text-base text-ink">{g}</span>
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.section
          key={active}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.22, ease: [0.2, 0.7, 0.2, 1] }}
          className="grid gap-6 lg:grid-cols-[minmax(0,_1fr)_minmax(0,_1.2fr)]"
        >
          {/* Standings projection */}
          <div className="card">
            <h2 className="mb-3 text-lg font-semibold tracking-tight">Group {active} · projection</h2>
            <ol className="space-y-2">
              {(standings[active] ?? []).map((row, i) => (
                <li
                  key={row.code}
                  className={cn(
                    "grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-xl border p-3 transition-colors duration-200",
                    i === 0
                      ? "border-pitch-500/40 bg-pitch-500/5"
                      : i === 1
                      ? "border-gold-500/40 bg-gold-500/5"
                      : i === 2
                      ? "border-line2/60 bg-elevated/40"
                      : "border-line/70 bg-surface2/30 opacity-80"
                  )}
                >
                  <span
                    aria-label={`Projected ${ordinal(i + 1)} place`}
                    className={cn(
                      "inline-flex h-7 w-7 items-center justify-center rounded-lg font-mono text-xs",
                      i === 0
                        ? "bg-pitch-500/20 text-pitch-400"
                        : i === 1
                        ? "bg-gold-500/20 text-gold-400"
                        : i === 2
                        ? "bg-line2/60 text-ink/80"
                        : "bg-line2/40 text-muted"
                    )}
                  >
                    {i === 0 ? <Crown className="h-3.5 w-3.5" /> : i === 1 ? <Medal className="h-3.5 w-3.5" /> : i === 2 ? <ShieldCheck className="h-3.5 w-3.5" /> : i + 1}
                  </span>
                  <TeamLabel code={row.code} name={names[row.code] ?? row.code} size="md" showCode />
                  <div className="hidden flex-col items-end font-mono text-[11px] text-muted sm:flex">
                    <span>
                      win <span className="text-ink">{pct(row.p1)}</span>
                    </span>
                    <span>
                      adv <span className="text-ink">{pct(row.p1 + row.p2)}</span>
                    </span>
                  </div>
                </li>
              ))}
            </ol>
            <div className="mt-3 text-[11px] text-muted">
              Top two advance directly. The eight best third-placed teams also go through.
            </div>

            <div className="mt-5">
              <div className="mb-2 text-[11px] uppercase tracking-widest text-muted">
                Finish-position breakdown
              </div>
              <div className="overflow-hidden rounded-xl border border-line/80">
                <table className="w-full text-xs">
                  <thead className="bg-elevated/60 text-muted">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">Team</th>
                      <th className="px-2 py-2 text-right font-medium">1st</th>
                      <th className="px-2 py-2 text-right font-medium">2nd</th>
                      <th className="px-2 py-2 text-right font-medium">3rd</th>
                      <th className="px-2 py-2 text-right font-medium">4th</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(standings[active] ?? []).map((row) => (
                      <tr key={row.code} className="border-t border-line/60">
                        <td className="px-3 py-1.5">
                          <TeamLabel code={row.code} name={names[row.code] ?? row.code} size="sm" />
                        </td>
                        <td className="px-2 py-1.5 text-right font-mono">{pct(row.p1)}</td>
                        <td className="px-2 py-1.5 text-right font-mono">{pct(row.p2)}</td>
                        <td className="px-2 py-1.5 text-right font-mono">{pct(row.p3)}</td>
                        <td className="px-2 py-1.5 text-right font-mono">{pct(row.p4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Match cards */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold tracking-tight">
                Group {active} · matches
              </h2>
              <span className="chip">
                <ArrowDown className="h-3 w-3" />
                by date
              </span>
            </div>
            <div className="grid gap-3">
              {(groupPredictions[active] ?? []).map((p, i) => (
                <MatchCard key={p.match_id} pred={p} names={names} index={i} />
              ))}
              {!(groupPredictions[active] ?? []).length ? (
                <div className="card text-sm text-muted">No fixtures for this group yet.</div>
              ) : null}
            </div>
          </div>
        </motion.section>
      </AnimatePresence>
    </div>
  );
}

function pct(p: number): string {
  if (!isFinite(p)) return "—";
  return (p * 100).toFixed(1) + "%";
}
function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}
