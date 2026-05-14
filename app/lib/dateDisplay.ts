/**
 * Deterministic date headings for the UI. Uses a fixed locale and noon UTC so
 * server HTML matches client hydration and does not depend on the visitor's
 * system locale or timezone edge cases around midnight.
 */
export function formatScheduleDayHeading(isoDate: string): string {
  const d = new Date(`${isoDate}T12:00:00Z`);
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}
