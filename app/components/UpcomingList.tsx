"use client";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { MatchCard } from "./MatchCard";
import { formatScheduleDayHeading } from "../lib/dateDisplay";
import type { Prediction } from "../lib/types";

export function UpcomingList({
  items,
  names,
  initialCount = 8,
}: {
  items: Prediction[];
  names: Record<string, string>;
  initialCount?: number;
}) {
  const [showAll, setShowAll] = useState(false);

  const buckets = useMemo(() => {
    const map = new Map<string, Prediction[]>();
    const sorted = [...items].sort((a, b) =>
      a.date < b.date ? -1 : a.date > b.date ? 1 : a.match_id.localeCompare(b.match_id)
    );
    for (const p of sorted) {
      const arr = map.get(p.date) ?? [];
      arr.push(p);
      map.set(p.date, arr);
    }
    const keys = Array.from(map.keys()).sort();
    return keys.map((k) => ({
      key: k,
      heading: formatScheduleDayHeading(k),
      items: map.get(k)!,
    }));
  }, [items]);

  const visible = useMemo(() => {
    if (showAll) return buckets;
    // Show first bucket(s) up to ~initialCount items, then collapse the rest
    const out: typeof buckets = [];
    let n = 0;
    for (const b of buckets) {
      if (n >= initialCount) break;
      const take = b.items.slice(0, initialCount - n);
      out.push({ key: b.key, heading: b.heading, items: take });
      n += take.length;
    }
    return out;
  }, [buckets, showAll, initialCount]);

  const hiddenCount = items.length - visible.reduce((s, b) => s + b.items.length, 0);

  return (
    <div className="space-y-7">
      {visible.map((b, gIdx) => (
        <section key={b.key} className="space-y-3">
          <div className="flex items-baseline gap-3">
            <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted">
              {b.heading}
            </h3>
            <span className="chip">{b.items.length} match{b.items.length === 1 ? "" : "es"}</span>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {b.items.map((p, i) => (
              <MatchCard key={p.match_id} pred={p} names={names} index={gIdx * 6 + i} />
            ))}
          </div>
        </section>
      ))}
      {!showAll && hiddenCount > 0 ? (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setShowAll(true)}
          className="btn mx-auto flex w-full max-w-xs"
        >
          Show {hiddenCount} more {hiddenCount === 1 ? "match" : "matches"}
          <ChevronDown className="h-4 w-4" />
        </motion.button>
      ) : null}
    </div>
  );
}
