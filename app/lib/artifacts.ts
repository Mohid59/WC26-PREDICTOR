import path from "node:path";
import { promises as fs } from "node:fs";
import type {
  PredictionsBundle,
  SimulationBundle,
  Team,
  Fixture,
  ModelInfo,
  DataStatus,
  Metrics,
} from "./types";

const DATA_DIR = path.join(process.cwd(), "public", "data");
const REPORTS_DIR = path.join(process.cwd(), "reports");

async function readJsonSafe<T>(file: string, fallback: T | null = null): Promise<T | null> {
  try {
    const raw = await fs.readFile(file, "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export async function loadPredictions(): Promise<PredictionsBundle | null> {
  return readJsonSafe<PredictionsBundle>(path.join(DATA_DIR, "predictions.json"));
}
export async function loadSimulation(): Promise<SimulationBundle | null> {
  return readJsonSafe<SimulationBundle>(path.join(DATA_DIR, "simulation.json"));
}
export async function loadTeams(): Promise<{ items: Team[] } | null> {
  return readJsonSafe<{ items: Team[] }>(path.join(DATA_DIR, "teams.json"));
}
export async function loadFixtures(): Promise<{ items: Fixture[] } | null> {
  return readJsonSafe<{ items: Fixture[] }>(path.join(DATA_DIR, "fixtures.json"));
}
export async function loadModelInfo(): Promise<ModelInfo | null> {
  return readJsonSafe<ModelInfo>(path.join(DATA_DIR, "model_info.json"));
}
export async function loadDataStatus(): Promise<DataStatus | null> {
  return readJsonSafe<DataStatus>(path.join(DATA_DIR, "data_status.json"));
}
export async function loadMetrics(): Promise<Metrics | null> {
  return readJsonSafe<Metrics>(path.join(REPORTS_DIR, "metrics.json"));
}

export function pct(p: number): string {
  return (p * 100).toFixed(1) + "%";
}

export function teamNameMap(teams: Team[] | undefined): Record<string, string> {
  const m: Record<string, string> = {};
  (teams ?? []).forEach((t) => (m[t.code] = t.name));
  return m;
}
