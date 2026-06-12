import Link from "next/link";
import { Users } from "lucide-react";
import { loadFixtures, loadSquads, loadTeams } from "../lib/artifacts";
import { Flag } from "../components/Flag";

export const dynamic = "force-static";

export default async function TeamsPage() {
  const [teams, fixtures, squads] = await Promise.all([
    loadTeams(),
    loadFixtures(),
    loadSquads(),
  ]);
  if (!teams) {
    return <div className="card">No teams available yet.</div>;
  }

  const groupOf: Record<string, string> = {};
  for (const f of fixtures?.items ?? []) {
    if (f.stage === "group" && f.group) {
      groupOf[f.home] = f.group;
      groupOf[f.away] = f.group;
    }
  }

  const byGroup = new Map<string, typeof teams.items>();
  for (const t of [...teams.items].sort((a, b) => a.name.localeCompare(b.name))) {
    const g = groupOf[t.code] ?? "?";
    const arr = byGroup.get(g) ?? [];
    arr.push(t);
    byGroup.set(g, arr);
  }
  const groups = Array.from(byGroup.keys()).sort();

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <div className="inline-flex items-center gap-2">
          <span className="h-1 w-12 rounded-full bg-gradient-cup" aria-hidden />
          <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-gold-400">
            Squads
          </span>
        </div>
        <h1 className="inline-flex items-center gap-3 text-3xl font-black tracking-tight md:text-5xl">
          <Users className="h-8 w-8 text-gold-500" aria-hidden /> All 48 teams
        </h1>
        <p className="text-sm text-muted">
          Official 26-man World Cup squads for every qualified nation. Tap a team for the full
          player list with caps, goals and clubs.
        </p>
      </header>

      <div className="space-y-7">
        {groups.map((g) => (
          <section key={g} className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted">
              Group {g}
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {(byGroup.get(g) ?? []).map((t) => {
                const squad = squads?.squads[t.code];
                return (
                  <Link
                    key={t.code}
                    href={`/teams/${encodeURIComponent(t.code)}`}
                    className="group flex items-center gap-3 rounded-2xl border border-line/80 bg-surface2/80 p-4 transition-colors duration-200 hover:border-gold-500/60 hover:bg-elevated/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-500"
                  >
                    <Flag code={t.code} name={t.name} size="lg" rounded="rounded-md" />
                    <div className="min-w-0">
                      <div className="truncate text-sm font-bold tracking-tight">{t.name}</div>
                      <div className="text-[11px] text-subtle">
                        {squad?.coach ? squad.coach : t.confederation}
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
