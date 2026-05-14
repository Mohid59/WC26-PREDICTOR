import { NextResponse } from "next/server";
import { loadPredictions } from "../../../lib/artifacts";

export async function GET(
  _req: Request,
  { params }: { params: { matchId: string } }
) {
  const data = await loadPredictions();
  if (!data) return NextResponse.json({ error: "no_artifacts" }, { status: 503 });
  const pred = data.items.find((p) => p.match_id === decodeURIComponent(params.matchId));
  if (!pred) return NextResponse.json({ error: "not_found" }, { status: 404 });
  return NextResponse.json({
    ...pred,
    model_version: data.model_version,
    generated_at: data.generated_at,
  });
}
