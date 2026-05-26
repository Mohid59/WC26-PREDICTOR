import Link from "next/link";
import { ArrowRight, Trophy, LayoutGrid, GitBranchPlus } from "lucide-react";
import {
  loadFixtures,
  loadPredictions,
  loadSimulation,
  loadTeams,
  teamNameMap,
} from "./lib/artifacts";
import { UpcomingList } from "./components/UpcomingList";
import { TopWinners } from "./components/TopWinners";
import { KickoffCountdown } from "./components/KickoffCountdown";

export const dynamic = "force-static";

const TOURNAMENT_START = "2026-06-11";

export default async function HomePage() {
  const [fixtures, preds, sim, teamsBundle] = await Promise.all([
    loadFixtures(),
    loadPredictions(),
    loadSimulation(),
    loadTeams(),
  ]);

  if (!preds || preds.items.length === 0) {
    return (
      <div className="card text-center">
        <h2 className="text-lg font-semibold">No predictions available yet</h2>
        <p className="mt-2 text-sm text-muted">Please check back shortly.</p>
      </div>
    );
  }

  const names = teamNameMap(teamsBundle?.items);

  const topWinners = sim
    ? (Object.entries(sim.round_probs)
        .sort((a, b) => b[1].winner - a[1].winner)
        .slice(0, 10) as Array<[string, { winner: number; sf: number; r16: number }]>)
    : [];

  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-line/80 bg-surface2/60 p-8 backdrop-blur md:p-10">
        <div className="pointer-events-none absolute -top-40 right-[-12%] h-[34rem] w-[34rem] rounded-full bg-crimson-700/25 blur-[140px]" />
        <div className="pointer-events-none absolute -bottom-40 left-[-12%] h-[34rem] w-[34rem] rounded-full bg-pitch-700/20 blur-[140px]" />
        <div className="pointer-events-none absolute right-10 top-10 h-32 w-32 rounded-full bg-gold-500/20 blur-3xl" />

        <div className="relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2">
            <span className="h-1 w-12 rounded-full bg-gradient-cup" aria-hidden />
            <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-gold-400">
              FIFA World Cup 2026 - USA - Mexico - Canada
            </span>
          </div>
          <h1 className="max-w-3xl text-4xl font-black tracking-tight md:text-6xl">
            Every match.{" "}
            <span className="bg-gradient-cup bg-clip-text text-transparent">Every probability.</span>
          </h1>
          <p className="max-w-2xl text-sm text-muted md:text-base">
            Official schedule coverage for all 104 matches, with group-stage forecasts and a Monte
            Carlo simulation of the full tournament path.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/fixtures" className="btn-primary">
              See all fixtures <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/groups" className="btn">
              <LayoutGrid className="h-4 w-4" /> Explore groups
            </Link>
            <Link href="/bracket" className="btn">
              <GitBranchPlus className="h-4 w-4" /> Bracket projection
            </Link>
          </div>

          {/* Countdown + headline numbers */}
          <div className="grid gap-3 pt-4 sm:grid-cols-3">
            <HeroStat
              label="Kickoff"
              value={<KickoffCountdown startIso={TOURNAMENT_START} />}
              sub="11 June 2026"
            />
            <HeroStat
              label="Matches"
              value={(fixtures?.items.length ?? 104).toString()}
              sub="official fixtures"
            />
            <HeroStat
              label="Simulations"
              value={sim ? sim.n_sims.toLocaleString() : "—"}
              sub="of the full tournament"
            />
          </div>
        </div>
      </section>

      {/* Upcoming */}
      <section className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-2xl font-bold tracking-tight">Upcoming matches</h2>
          <Link href="/fixtures" className="text-sm text-gold-400 hover:underline">
            All fixtures →
          </Link>
        </div>
        <UpcomingList items={preds.items} names={names} initialCount={8} />
      </section>

      {/* Top winners */}
      {topWinners.length ? (
        <section className="space-y-4">
          <div className="flex items-baseline justify-between">
            <h2 className="text-2xl font-bold tracking-tight">
              <span className="inline-flex items-center gap-2">
                <Trophy className="h-5 w-5 text-gold-500" /> Title contenders
              </span>
            </h2>
            <Link href="/bracket" className="text-sm text-gold-400 hover:underline">
              Full bracket →
            </Link>
          </div>
          <TopWinners items={topWinners} names={names} total={sim?.n_sims} />
        </section>
      ) : null}
    </div>
  );
}

function HeroStat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="rounded-2xl border border-line/80 bg-surface2/60 p-4 backdrop-blur">
      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted">
        {label}
      </div>
      <div className="mt-1 font-display text-2xl font-extrabold tracking-tight md:text-3xl">
        {value}
      </div>
      {sub ? <div className="mt-0.5 text-xs text-muted">{sub}</div> : null}
    </div>
  );
}
