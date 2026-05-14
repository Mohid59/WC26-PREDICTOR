import { loadPredictions, loadSimulation, loadTeams, teamNameMap } from "../lib/artifacts";
import { GroupsTabs } from "../components/GroupsTabs";
import type { Prediction } from "../lib/types";

export const dynamic = "force-static";

export default async function GroupsPage() {
  const [preds, sim, teamsBundle] = await Promise.all([
    loadPredictions(),
    loadSimulation(),
    loadTeams(),
  ]);

  if (!preds) {
    return (
      <div className="card">
        No predictions yet. Run <code className="font-mono">npm run ml:pipeline</code>.
      </div>
    );
  }

  const names = teamNameMap(teamsBundle?.items);

  // Group predictions by group letter, preserving date order
  const groupPredictions: Record<string, Prediction[]> = {};
  for (const p of preds.items) {
    if (p.stage !== "group" || !p.group) continue;
    (groupPredictions[p.group] ??= []).push(p);
  }
  for (const g of Object.keys(groupPredictions)) {
    groupPredictions[g].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : a.match_id.localeCompare(b.match_id)));
  }

  const groupKeys = Object.keys(groupPredictions).sort();

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <div className="inline-flex items-center gap-2">
          <span className="h-1 w-12 rounded-full bg-gradient-cup" aria-hidden />
          <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-gold-400">
            Group stage
          </span>
        </div>
        <h1 className="text-3xl font-black tracking-tight md:text-5xl">All twelve groups</h1>
        <p className="max-w-2xl text-sm text-muted">
          Projected finishing positions and the six matches for every group. Top two advance —
          the eight best third-placed teams also go through.
        </p>
      </header>

      <GroupsTabs
        groupKeys={groupKeys}
        groupPredictions={groupPredictions}
        groupFinish={sim?.group_finish ?? {}}
        names={names}
      />
    </div>
  );
}
