"use client";
import { useEffect, useState } from "react";

function computeDays(startIso: string): number {
  return Math.max(
    0,
    Math.round((new Date(startIso + "T00:00:00").getTime() - Date.now()) / 86_400_000)
  );
}

export function KickoffCountdown({ startIso }: { startIso: string }) {
  const [days, setDays] = useState(() => computeDays(startIso));

  useEffect(() => {
    setDays(computeDays(startIso));
    const id = setInterval(() => setDays(computeDays(startIso)), 60_000);
    return () => clearInterval(id);
  }, [startIso]);

  return <>{days > 0 ? `${days} days` : "Live"}</>;
}
