"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, CalendarDays, Clock, MapPin } from "lucide-react";
import { ProbBar } from "./ProbBar";
import { TeamLabel } from "./TeamLabel";
import { cn } from "../lib/cn";
import { formatScheduleDayHeading } from "../lib/dateDisplay";
import { headlineScoreline } from "../lib/predictionDisplay";
import type { Fixture, Prediction } from "../lib/types";

const STAGE_LABELS: Record<string, string> = {
  group: "Group",
  r32: "Round of 32",
  r16: "Round of 16",
  qf: "Quarter-final",
  sf: "Semi-final",
  third: "Third place",
  final: "Final",
};

function matchNumber(matchId: string): string {
  const n = Number(matchId.replace(/\D/g, ""));
  return Number.isFinite(n) && n > 0 ? `Match ${n}` : matchId;
}

function stageLabel(fixture: Fixture): string {
  if (fixture.stage === "group") return `Group ${fixture.group ?? ""}`.trim();
  return STAGE_LABELS[fixture.stage] ?? fixture.stage.toUpperCase();
}

function sortFixtures(a: Fixture, b: Fixture): number {
  if (a.date !== b.date) return a.date < b.date ? -1 : 1;
  const ak = a.kickoff ?? "";
  const bk = b.kickoff ?? "";
  if (ak !== bk) return ak < bk ? -1 : 1;
  return a.match_id.localeCompare(b.match_id);
}

function TeamSlot({
  code,
  names,
  align = "left",
}: {
  code: string;
  names: Record<string, string>;
  align?: "left" | "right";
}) {
  const name = names[code];
  if (name) {
    return <TeamLabel code={code} name={name} size="md" align={align} />;
  }
  return (
    <div
      className={cn(
        "min-w-0 text-sm font-semibold tracking-tight text-muted",
        align === "right" && "text-right"
      )}
    >
      <span className="line-clamp-2">{code}</span>
    </div>
  );
}

function FixtureCard({
  fixture,
  pred,
  names,
  index,
}: {
  fixture: Fixture;
  pred?: Prediction;
  names: Record<string, string>;
  index: number;
}) {
  const top = pred ? headlineScoreline(pred) : undefined;
  const homeName = names[fixture.home] ?? fixture.home;
  const awayName = names[fixture.away] ?? fixture.away;
  const content = (
    <>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
        <span className="inline-flex flex-wrap items-center gap-1.5">
          <span className="chip border-gold-500/40 text-gold-400">{stageLabel(fixture)}</span>
          <span className="chip">{matchNumber(fixture.match_id)}</span>
        </span>
        <span className="inline-flex items-center gap-1">
          <Clock className="h-3 w-3" /> {fixture.date}
          {fixture.kickoff ? ` - ${fixture.kickoff}` : ""}
        </span>
      </div>

      <div className="mb-3 grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3">
        <TeamSlot code={fixture.home} names={names} />
        <div className="text-center text-[11px] uppercase tracking-widest text-subtle">vs</div>
        <TeamSlot code={fixture.away} names={names} align="right" />
      </div>

      {pred ? <ProbBar pHome={pred.p_home} pDraw={pred.p_draw} pAway={pred.p_away} /> : null}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted">
        {top ? (
          <span>
            Most likely scoreline{" "}
            <span className="rounded-md border border-line/80 bg-elevated px-1.5 py-0.5 font-mono text-ink tabular-nums">
              {top.home_goals}-{top.away_goals}
            </span>
          </span>
        ) : (
          <span className="inline-flex items-center gap-1">
            <CalendarDays className="h-3 w-3" /> Official fixture slot
          </span>
        )}
        {pred ? (
          <span className="inline-flex items-center gap-1 text-gold-400 transition-transform duration-200 group-hover:translate-x-0.5">
            details <ArrowRight className="h-3 w-3" />
          </span>
        ) : null}
      </div>

      {fixture.venue ? (
        <div className="mt-2 inline-flex items-center gap-1 text-[11px] text-subtle">
          <MapPin className="h-3 w-3" /> {fixture.venue}
        </div>
      ) : null}
    </>
  );

  const className = cn(
    "group relative block rounded-2xl border border-line/80 bg-surface2/80 p-4",
    "transition-colors duration-200 hover:border-gold-500/60 hover:bg-elevated/90",
    pred && "cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-500"
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.32, delay: (index % 8) * 0.025, ease: [0.2, 0.7, 0.2, 1] }}
    >
      {pred ? (
        <Link
          href={`/match/${encodeURIComponent(pred.match_id)}`}
          className={className}
          aria-label={`${homeName} vs ${awayName}, ${fixture.date}`}
        >
          {content}
        </Link>
      ) : (
        <div className={className}>{content}</div>
      )}
    </motion.div>
  );
}

export function FixtureScheduleList({
  items,
  predictions,
  names,
}: {
  items: Fixture[];
  predictions: Prediction[];
  names: Record<string, string>;
}) {
  const predictionById = new Map(predictions.map((p) => [p.match_id, p]));
  const sorted = [...items].sort(sortFixtures);
  const groups: { date: string; fixtures: Fixture[] }[] = [];
  for (const fixture of sorted) {
    const last = groups[groups.length - 1];
    if (last && last.date === fixture.date) {
      last.fixtures.push(fixture);
    } else {
      groups.push({ date: fixture.date, fixtures: [fixture] });
    }
  }

  return (
    <div className="space-y-7">
      {groups.map((group, groupIndex) => (
        <section key={group.date} className="space-y-3">
          <div className="flex items-baseline gap-3">
            <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted">
              {formatScheduleDayHeading(group.date)}
            </h3>
            <span className="chip">
              {group.fixtures.length} match{group.fixtures.length === 1 ? "" : "es"}
            </span>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {group.fixtures.map((fixture, itemIndex) => (
              <FixtureCard
                key={`${fixture.match_id}-${fixture.stage}`}
                fixture={fixture}
                pred={predictionById.get(fixture.match_id)}
                names={names}
                index={groupIndex * 8 + itemIndex}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
