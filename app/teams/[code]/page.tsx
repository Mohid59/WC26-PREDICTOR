import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, UserRound } from "lucide-react";
import { loadFixtures, loadSquads, loadTeams } from "../../lib/artifacts";
import { Flag } from "../../components/Flag";
import type { SquadPlayer } from "../../lib/types";

export const dynamic = "force-static";

const POSITION_ORDER: Array<{ key: string; label: string }> = [
  { key: "GK", label: "Goalkeepers" },
  { key: "DF", label: "Defenders" },
  { key: "MF", label: "Midfielders" },
  { key: "FW", label: "Forwards" },
];

export async function generateStaticParams() {
  const teams = await loadTeams();
  return (teams?.items ?? []).map((t) => ({ code: t.code }));
}

export default async function TeamSquadPage({ params }: { params: { code: string } }) {
  const code = decodeURIComponent(params.code).toUpperCase();
  const [teams, squads, fixtures] = await Promise.all([
    loadTeams(),
    loadSquads(),
    loadFixtures(),
  ]);
  const team = teams?.items.find((t) => t.code === code);
  if (!team) return notFound();
  const squad = squads?.squads[code];

  const group =
    fixtures?.items.find(
      (f) => f.stage === "group" && (f.home === code || f.away === code)
    )?.group ?? null;

  return (
    <article className="space-y-8">
      <header className="space-y-4">
        <Link
          href="/teams"
          className="inline-flex items-center gap-1 text-sm text-gold-400 hover:underline"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> All teams
        </Link>

        <div className="relative overflow-hidden rounded-3xl border border-line/80 bg-surface2/60 p-6 backdrop-blur md:p-8">
          <div className="pointer-events-none absolute -top-32 right-[-15%] h-[20rem] w-[20rem] rounded-full bg-gold-500/15 blur-3xl" />
          <div className="relative z-10 flex flex-wrap items-center gap-5">
            <Flag code={code} name={team.name} size="xl" rounded="rounded-md" />
            <div>
              <h1 className="text-3xl font-black tracking-tight md:text-5xl">{team.name}</h1>
              <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-muted">
                {group ? <span className="chip border-gold-500/40 text-gold-400">Group {group}</span> : null}
                <span className="chip">{team.confederation}</span>
                {squad?.coach ? (
                  <span className="inline-flex items-center gap-1">
                    <UserRound className="h-3.5 w-3.5" /> Coach{" "}
                    <span className="font-semibold text-ink">{squad.coach}</span>
                  </span>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </header>

      {!squad ? (
        <div className="card text-sm text-muted">Official squad not available yet.</div>
      ) : (
        <div className="space-y-6">
          {POSITION_ORDER.map(({ key, label }) => {
            const players = squad.players.filter((p) => p.position === key);
            if (!players.length) return null;
            return (
              <section key={key} className="card overflow-x-auto">
                <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-muted">
                  {label}
                </h2>
                <table className="w-full min-w-[34rem] text-left text-sm">
                  <thead>
                    <tr className="text-[11px] uppercase tracking-wider text-subtle">
                      <th className="w-10 pb-2 font-semibold">#</th>
                      <th className="pb-2 font-semibold">Player</th>
                      <th className="w-14 pb-2 text-right font-semibold">Age</th>
                      <th className="w-14 pb-2 text-right font-semibold">Caps</th>
                      <th className="w-14 pb-2 text-right font-semibold">Goals</th>
                      <th className="w-[35%] pb-2 pl-4 font-semibold">Club</th>
                    </tr>
                  </thead>
                  <tbody>
                    {players.map((p) => (
                      <PlayerRow key={`${p.number}-${p.name}`} p={p} />
                    ))}
                  </tbody>
                </table>
              </section>
            );
          })}
          <p className="text-xs text-subtle">
            Source: official FIFA squad lists{" "}
            {squads?.generated_at ? `· synced ${squads.generated_at.slice(0, 10)}` : ""}
          </p>
        </div>
      )}
    </article>
  );
}

function PlayerRow({ p }: { p: SquadPlayer }) {
  return (
    <tr className="border-t border-line/60">
      <td className="py-2 font-mono text-subtle tabular-nums">{p.number ?? "—"}</td>
      <td className="py-2 font-semibold">{p.name}</td>
      <td className="py-2 text-right font-mono tabular-nums">{p.age ?? "—"}</td>
      <td className="py-2 text-right font-mono tabular-nums">{p.caps ?? "—"}</td>
      <td className="py-2 text-right font-mono tabular-nums">{p.goals ?? "—"}</td>
      <td className="py-2 pl-4 text-muted">{p.club ?? "—"}</td>
    </tr>
  );
}
