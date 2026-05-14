import { NextResponse } from "next/server";
import { loadMetrics } from "../../../lib/artifacts";

export async function GET() {
  const data = await loadMetrics();
  if (!data) return NextResponse.json({ error: "no_artifacts" }, { status: 503 });
  return NextResponse.json(data);
}
