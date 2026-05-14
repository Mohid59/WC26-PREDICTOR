import { NextResponse } from "next/server";
import { spawn } from "node:child_process";
import path from "node:path";

/**
 * Local-only admin endpoint. Refuses on non-local hosts unless explicitly
 * enabled via ADMIN_REFRESH_TOKEN. Documented as a development convenience.
 */
export async function POST(req: Request) {
  const url = new URL(req.url);
  const host = req.headers.get("host") ?? "";
  const isLocal =
    host.startsWith("localhost") || host.startsWith("127.0.0.1") || host.startsWith("0.0.0.0");

  const token = process.env.ADMIN_REFRESH_TOKEN;
  const provided = req.headers.get("x-admin-token");
  if (!isLocal && (!token || token !== provided)) {
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  }

  return new Promise<Response>((resolve) => {
    const py = spawn(process.platform === "win32" ? "python" : "python3",
      [path.join("ml", "scripts", "run_pipeline.py")],
      { cwd: process.cwd() }
    );
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
