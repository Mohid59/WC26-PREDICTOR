"use client";
import { motion } from "framer-motion";
import { Trophy } from "lucide-react";
import { TeamLabel } from "./TeamLabel";

export function TopWinners({
  items,
  names,
}: {
  items: Array<[string, { winner: number; sf: number; r16: number }]>;
  names: Record<string, string>;
  total?: number;
}) {
  if (!items.length) return null;
  const max = items[0][1].winner;
  return (
    <div className="card">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="inline-flex items-center gap-2 text-lg font-semibold tracking-tight">
          <Trophy className="h-4 w-4 text-gold-500" /> Title odds
        </h2>
      </div>
      <ol className="space-y-2.5">
        {items.map(([code, probs], i) => (
          <li key={code} className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3">
            <span className="w-6 text-center font-mono text-xs text-subtle">{i + 1}</span>
            <div className="min-w-0">
              <TeamLabel code={code} name={names[code] ?? code} size="sm" />
              <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-line/80">
                <motion.div
                  initial={{ width: 0 }}
                  whileInView={{ width: `${Math.min((probs.winner / max) * 100, 100)}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.7, delay: i * 0.04, ease: [0.2, 0.7, 0.2, 1] }}
                  className="h-full rounded-full bg-gradient-cup"
                />
              </div>
            </div>
            <div className="w-20 text-right">
              <div className="font-mono text-sm text-ink">{(probs.winner * 100).toFixed(1)}%</div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
