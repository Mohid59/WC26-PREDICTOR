import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Calendar, MapPin, Clock, Activity, ListTree, Lightbulb } from "lucide-react";
import {
  loadPredictions,
  loadTeams,
  pct,
  teamNameMap,
} from "../../lib/artifacts";
import { ProbBar } from "../../components/ProbBar";
import { Flag } from "../../components/Flag";
import { describeFeature } from "../../lib/featureLabels";
import { orderedLikelyScores } from "../../lib/predictionDisplay";
import type { Prediction } from "../../lib/types";

export const dynamic = "force-static";

export async function generateStaticParams() {
  const preds = await loadPredictions();
  return (preds?.items ?? []).map((p) => ({ matchId: p.match_id }));
}

export default async function MatchPage({ params }: { params: { matchId: string } }) {
  const [preds, teams] = await Promise.all([loadPredictions(), loadTeams()]);
  if (!preds) return notFound();
  const pred = preds.items.find((p) => p.match_id === decodeURIComponent(params.matchId));
  if (!pred) return notFound();
  const names = teamNameMap(teams?.items);
  const homeName = names[pred.home] ?? pred.home;
  const awayName = names[pred.away] ?? pred.away;
  const verdict = pickVerdict(pred, homeName, awayName);
  const confidenceLabel = labelForConfidence(pred.confidence);
  const scorelines = orderedLikelyScores(pred);
  const headline = scorelines[0];

  return (
    <article className="space-y-8">
      <header className="space-y-4">
        <Link
          href="/fixtures"
          className="inline-flex items-center gap-1 text-sm text-gold-400 hover:underline"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> All fixtures
        </Link>
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
          <span className="chip border-gold-500/40 text-gold-400">
            {pred.stage === "group" ? `Group ${pred.group}` : pred.stage.toUpperCase()}
          </span>
          <span className="inline-flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" /> {formatDate(pred.date)}
          </span>
          {pred.kickoff ? (
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" /> {pred.kickoff}
            </span>
          ) : null}
          {pred.venue ? (
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" /> {pred.venue}
            </span>
          ) : null}
        </div>

        <div className="relative overflow-hidden rounded-3xl border border-line/80 bg-surface2/60 p-6 backdrop-blur md:p-8">
          <div className="pointer-events-none absolute -top-32 right-[-15%] h-[20rem] w-[20rem] rounded-full bg-gold-500/15 blur-3xl" />
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
            <div className="flex flex-col items-end gap-3 text-right">
              <Flag code={pred.home} name={homeName} size="xl" rounded="rounded-md" />
              <h2 className="text-2xl font-black tracking-tight md:text-4xl">{homeName}</h2>
            </div>
            <div className="text-center">
              <div className="text-[10px] uppercase tracking-[0.22em] text-muted">vs</div>
              <div className="mt-1 font-mono text-3xl font-extrabold tabular-nums text-ink md:text-5xl">
                {headline ? headline.home_goals : Math.round(pred.xg_home)}
                <span className="px-2 text-subtle">–</span>
                {headline ? headline.away_goals : Math.round(pred.xg_away)}
              </div>
              <div className="mt-0.5 text-[10px] uppercase tracking-[0.22em] text-subtle">
                most likely scoreline
              </div>
              <div className="mt-1.5 text-xs text-muted">
                Expected goals (Poisson): {pred.xg_home.toFixed(2)} – {pred.xg_away.toFixed(2)}
              </div>
            </div>
            <div className="flex flex-col items-start gap-3">
              <Flag code={pred.away} name={awayName} size="xl" rounded="rounded-md" />
              <h2 className="text-2xl font-black tracking-tight md:text-4xl">{awayName}</h2>
            </div>
          </div>
        </div>
      </header>

      <section className="card">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-muted">
            <Activity className="h-4 w-4" /> Win &middot; Draw &middot; Win
          </h2>
          <span className={`chip ${confidenceLabel.color}`}>{confidenceLabel.text}</span>
        </div>
        <ProbBar
          pHome={pred.p_home}
          pDraw={pred.p_draw}
          pAway={pred.p_away}
          homeLabel={homeName}
          awayLabel={awayName}
        />
        <p className="mt-3 text-sm">{verdict}</p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="card">
          <h2 className="mb-3 inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-muted">
            <ListTree className="h-4 w-4" /> Most likely scorelines
          </h2>
          <ol className="space-y-2">
            {scorelines.map((s, i) => (
              <li key={i} className="grid grid-cols-[auto_1fr_auto] items-center gap-3">
                <span className="rounded-md border border-line/80 bg-elevated px-2 py-1 font-mono text-sm tabular-nums">
                  {s.home_goals}–{s.away_goals}
                </span>
                <div className="prob-bar">
                  <div
                    className="h-full rounded-full bg-gradient-cup"
                    style={{ width: `${Math.min(s.prob * 100 * 4, 100)}%` }}
                  />
                </div>
                <span className="w-16 text-right font-mono text-sm">{pct(s.prob)}</span>
              </li>
            ))}
          </ol>
        </div>

        <div className="card">
          <h2 className="mb-3 inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-muted">
            <Lightbulb className="h-4 w-4" /> What's driving the pick
          </h2>
          {pred.top_features.length === 0 ? (
            <p className="text-sm text-muted">No factors available for this match.</p>
          ) : (
            <ul className="space-y-2.5">
              {pred.top_features.slice(0, 4).map((f, i) => {
                const meta = describeFeature(f.name, f.contribution);
                const positive = f.contribution >= 0;
                return (
                  <li key={i} className="rounded-xl border border-line/70 bg-surface2/40 p-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={
                          "inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded px-1 text-[10px] font-bold uppercase " +
                          (positive
                            ? "bg-pitch-500/20 text-pitch-400"
                            : "bg-crimson-500/20 text-crimson-400")
                        }
                      >
                        {positive ? "for" : "against"}
                      </span>
                      <span className="text-sm font-semibold">{meta.label}</span>
                    </div>
                    <p className="mt-1 text-xs text-muted">{meta.explanation}.</p>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-line/60 bg-surface2/40 p-4 text-xs text-muted">
        Probabilities are calibrated estimates from a model trained on historical international
        match data. They are not guarantees and not betting advice.
      </section>
    </article>
  );
}

function pickVerdict(p: Prediction, homeName: string, awayName: string): string {
  const max = Math.max(p.p_home, p.p_draw, p.p_away);
  const margin = max - Math.min(p.p_home, p.p_draw, p.p_away);
  const who =
    max === p.p_home
      ? `${homeName} favoured`
      : max === p.p_away
      ? `${awayName} favoured`
      : "very tight match";
  if (margin < 0.1) return `Too close to call — slight lean toward ${who.toLowerCase()}.`;
  return `${who}. Draw chance ${(p.p_draw * 100).toFixed(0)}%.`;
}

function labelForConfidence(c: number): { text: string; color: string } {
  if (c >= 0.55) return { text: "High confidence", color: "border-pitch-500/40 text-pitch-400" };
  if (c >= 0.3) return { text: "Moderate confidence", color: "border-gold-500/40 text-gold-400" };
  return { text: "Low confidence", color: "border-crimson-500/40 text-crimson-400" };
}

function formatDate(iso: string): string {
  try {
    const d = new Date(`${iso}T12:00:00Z`);
    return d.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}
