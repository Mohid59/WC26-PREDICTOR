import { CalendarDays } from "lucide-react";
import { loadFixtures, loadPredictions, loadTeams, teamNameMap } from "../lib/artifacts";
import { FixtureScheduleList } from "../components/FixtureScheduleList";

export const dynamic = "force-static";

export default async function FixturesPage() {
  const [fixtures, preds, teams] = await Promise.all([
    loadFixtures(),
    loadPredictions(),
    loadTeams(),
  ]);
  if (!fixtures) {
    return <div className="card">No fixtures available yet.</div>;
  }
  const names = teamNameMap(teams?.items);
  const forecastCount = preds?.items.length ?? 0;

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <div className="inline-flex items-center gap-2">
          <span className="h-1 w-12 rounded-full bg-gradient-cup" aria-hidden />
          <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-gold-400">
            Schedule
          </span>
        </div>
        <h1 className="inline-flex items-center gap-3 text-3xl font-black tracking-tight md:text-5xl">
          <CalendarDays className="h-8 w-8 text-gold-500" aria-hidden /> All fixtures
        </h1>
        <p className="text-sm text-muted">
          {fixtures.items.length} official matches across the full tournament. Kickoff times are
          shown in each venue's local time; {forecastCount} group-stage forecast cards link to the
          model details.
        </p>
      </header>

      <FixtureScheduleList
        items={fixtures.items}
        predictions={preds?.items ?? []}
        names={names}
      />
    </div>
  );
}
