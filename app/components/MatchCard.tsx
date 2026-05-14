"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { Clock, MapPin, ArrowRight } from "lucide-react";
import { ProbBar } from "./ProbBar";
import { TeamLabel } from "./TeamLabel";
import { cn } from "../lib/cn";
import { headlineScoreline } from "../lib/predictionDisplay";
import type { Prediction } from "../lib/types";

export function MatchCard({
  pred,
  names,
  index = 0,
}: {
  pred: Prediction;
  names: Record<string, string>;
  index?: number;
}) {
  const top = headlineScoreline(pred);
  const homeName = names[pred.home] ?? pred.home;
  const awayName = names[pred.away] ?? pred.away;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.32, delay: index * 0.025, ease: [0.2, 0.7, 0.2, 1] }}
    >
      <Link
        href={`/match/${encodeURIComponent(pred.match_id)}`}
        className={cn(
          "group relative block cursor-pointer rounded-2xl border border-line/80 bg-surface2/80 p-4",
          "transition-colors duration-200 hover:border-gold-500/60 hover:bg-elevated/90",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-500"
        )}
        aria-label={`${homeName} vs ${awayName}, ${pred.date}`}
      >
        <div className="mb-3 flex items-center justify-between text-xs text-muted">
          <span className="inline-flex items-center gap-1.5">
            <span className="chip border-gold-500/40 text-gold-400">
              {pred.stage === "group" ? `Group ${pred.group}` : pred.stage.toUpperCase()}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" /> {pred.date}
              {pred.kickoff ? ` · ${pred.kickoff}` : ""}
            </span>
          </span>
          <span className="chip">
            conf <span className="ml-1 font-mono text-ink">{Math.round(pred.confidence * 100)}%</span>
          </span>
        </div>

        <div className="mb-3 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          <TeamLabel code={pred.home} name={homeName} size="md" />
          <div className="text-center text-[11px] uppercase tracking-widest text-subtle">vs</div>
          <TeamLabel code={pred.away} name={awayName} size="md" align="right" />
        </div>

        <ProbBar pHome={pred.p_home} pDraw={pred.p_draw} pAway={pred.p_away} />

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
          {top ? (
            <span>
              Most likely scoreline{" "}
              <span className="rounded-md border border-line/80 bg-elevated px-1.5 py-0.5 font-mono text-ink tabular-nums">
                {top.home_goals}–{top.away_goals}
              </span>
            </span>
          ) : null}
          <span className="inline-flex items-center gap-1 text-gold-400 transition-transform duration-200 group-hover:translate-x-0.5">
            details <ArrowRight className="h-3 w-3" />
          </span>
        </div>
        {pred.venue ? (
          <div className="mt-2 inline-flex items-center gap-1 text-[11px] text-subtle">
            <MapPin className="h-3 w-3" /> {pred.venue}
          </div>
        ) : null}
      </Link>
    </motion.div>
  );
}
