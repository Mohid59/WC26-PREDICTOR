"use client";
import { motion } from "framer-motion";

export function ProbBar({
  pHome,
  pDraw,
  pAway,
  homeLabel,
  awayLabel,
  size = "md",
}: {
  pHome: number;
  pDraw: number;
  pAway: number;
  homeLabel?: string;
  awayLabel?: string;
  size?: "sm" | "md";
}) {
  const fmt = (p: number) => `${(p * 100).toFixed(1)}%`;
  const h = (pHome * 100).toFixed(2);
  const d = (pDraw * 100).toFixed(2);
  const a = (pAway * 100).toFixed(2);
  const cls = size === "sm" ? "h-1.5" : "h-2.5";
  return (
    <div className="space-y-1.5">
      <div
        className={`flex w-full overflow-hidden rounded-full bg-line/80 ${cls}`}
        role="img"
        aria-label={`win probability ${homeLabel ?? "home"} ${fmt(pHome)}, draw ${fmt(pDraw)}, ${awayLabel ?? "away"} ${fmt(pAway)}`}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${h}%` }}
          transition={{ duration: 0.6, ease: [0.2, 0.7, 0.2, 1] }}
          className="bg-home"
        />
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${d}%` }}
          transition={{ duration: 0.6, delay: 0.05, ease: [0.2, 0.7, 0.2, 1] }}
          className="bg-draw"
        />
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${a}%` }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.2, 0.7, 0.2, 1] }}
          className="bg-away"
        />
      </div>
      <div className="flex justify-between font-mono text-[11px] text-muted">
        <span className="text-home">{fmt(pHome)}</span>
        <span>Draw {fmt(pDraw)}</span>
        <span className="text-away">{fmt(pAway)}</span>
      </div>
    </div>
  );
}
