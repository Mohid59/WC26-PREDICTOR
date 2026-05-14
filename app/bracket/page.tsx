import { Trophy } from "lucide-react";
import { loadSimulation, loadTeams, pct, teamNameMap } from "../lib/artifacts";
import { TeamLabel } from "../components/TeamLabel";

export const dynamic = "force-static";

const ROUND_LABELS: Array<[keyof BracketRow, string]> = [
  ["r32", "R32"],
  ["r16", "R16"],
  ["qf", "QF"],
  ["sf", "SF"],
  ["final", "Final"],
  ["winner", "Winner"],
];

type BracketRow = {
  group_play: number;
  r32: number;
  r16: number;
  qf: number;
  sf: number;
  final: number;
  winner: number;
};

export default async function BracketPage() {
  const [sim, teams] = await Promise.all([loadSimulation(), loadTeams()]);
  if (!sim) {
    return (
      <div className="card">
        No simulation yet. Run <code className="font-mono">npm run ml:pipeline</code>.
      </div>
    );
  }
  const names = teamNameMap(teams?.items);
  const nameOf = (c: string) => names[c] ?? c;

  const rows = Object.entries(sim.round_probs).sort((a, b) => b[1].winner - a[1].winner);

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <div className="inline-flex items-center gap-2">
          <span className="h-1 w-12 rounded-full bg-gradient-cup" aria-hidden />
          <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-gold-400">
            Bracket projection
          </span>
        </div>
        <h1 className="inline-flex items-center gap-3 text-3xl font-black tracking-tight md:text-5xl">
          <Trophy className="h-8 w-8 text-gold-500" aria-hidden /> The road to the final
        </h1>
        <p className="text-sm text-muted">
          Probability each team is still in the tournament going into each round.
        </p>
      </header>

      <section className="card">
        <h2 className="mb-4 text-lg font-semibold tracking-tight">Advance probability by round</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-line2 text-[11px] uppercase tracking-widest text-muted">
              <tr>
                <th className="py-2 text-left font-medium">Team</th>
                {ROUND_LABELS.map(([k, label]) => (
                  <th key={k} className="py-2 text-right font-medium">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(([code, probs]) => (
                <tr
                  key={code}
                  className="border-b border-line/60 transition-colors duration-200 hover:bg-elevated/60"
                >
                  <td className="py-2 pr-3">
                    <TeamLabel code={code} name={nameOf(code)} size="sm" />
                  </td>
                  {ROUND_LABELS.map(([k]) => {
                    const v = probs[k];
                    const intensity = Math.min(v * 100, 100);
                    return (
                      <td key={k} className="py-2 text-right">
                        <span
                          className="inline-block rounded-md px-2 py-0.5 font-mono text-xs tabular-nums"
                          style={{
                            background:
                              v > 0
                                ? `rgba(234,179,8,${0.08 + (intensity / 100) * 0.36})`
                                : "transparent",
                            color: v > 0.4 ? "#fef3c7" : v > 0.1 ? "#fde68a" : "#94a3a8",
                          }}
                        >
                          {pct(v)}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-muted">
          R32 includes the top 2 from every group plus the 8 best third-placed teams.
        </p>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold tracking-tight">Group standings projection</h2>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {Object.entries(sim.group_finish)
            .sort()
            .map(([group, teamsMap]) => (
              <div key={group} className="card">
                <div className="mb-2 flex items-center justify-between">
                  <div className="text-sm font-semibold">Group {group}</div>
                  <span className="chip font-mono text-[10px]">{group}</span>
                </div>
                <table className="w-full text-xs">
                  <thead className="text-[10px] uppercase tracking-widest text-muted">
                    <tr>
                      <th className="text-left font-medium">Team</th>
                      <th className="text-right font-medium">1st</th>
                      <th className="text-right font-medium">2nd</th>
                      <th className="text-right font-medium">3rd</th>
                      <th className="text-right font-medium">4th</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(teamsMap)
                      .sort((a, b) => (b[1]["1"] ?? 0) - (a[1]["1"] ?? 0))
                      .map(([code, posMap]) => (
                        <tr key={code} className="border-t border-line/60">
                          <td className="py-1.5 pr-2">
                            <TeamLabel code={code} name={nameOf(code)} size="sm" />
                          </td>
                          {[1, 2, 3, 4].map((pos) => (
                            <td key={pos} className="py-1.5 text-right font-mono tabular-nums">
                              {pct(posMap[String(pos)] ?? 0)}
                            </td>
                          ))}
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            ))}
        </div>
      </section>
    </div>
  );
}
