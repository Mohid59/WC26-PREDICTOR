import { NextResponse } from "next/server";
import { loadSimulation } from "../../lib/artifacts";

export async function GET() {
  const data = await loadSimulation();
  if (!data) return NextResponse.json({ error: "no_artifacts" }, { status: 503 });
  return NextResponse.json(data);
}

import { spawn } from "node:child_process";
import path from "node:path";
import { z } from "zod";

const RunSchema = z.object({
  n_sims: z.number().int().min(100).max(50000).optional(),
  seed: z.number().int().optional(),
});

export async function POST(req: Request) {
  let body: unknown = {};
  try {
    body = await req.json();
  } catch {
    // empty body allowed
  }
  const parsed = RunSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "invalid_body", details: parsed.error.format() }, { status: 400 });
  }
  const args = [
    path.join("ml", "scripts", "simulate_tournament.py"),
  ];
  if (parsed.data.n_sims) args.push("--n-sims", String(parsed.data.n_sims));
  if (parsed.data.seed !== undefined) args.push("--seed", String(parsed.data.seed));

  return new Promise<Response>((resolve) => {
    const py = spawn(process.platform === "win32" ? "python" : "python3", args, {
      cwd: process.cwd(),
    });
    let out = "";
    let err = "";
    py.stdout.on("data", (d) => (out += d.toString()));
    py.stderr.on("data", (d) => (err += d.toString()));
    py.on("close", (code) => {
      if (code === 0) {
        resolve(NextResponse.json({ ok: true, log: out.slice(-2000) }));
      } else {
        resolve(NextResponse.json({ ok: false, code, log: (out + err).slice(-2000) }, { status: 500 }));
      }
    });
  });
}
