import { Info } from "lucide-react";
import { loadDataStatus } from "../lib/artifacts";

export async function SampleDataBanner() {
  const status = await loadDataStatus();
  if (!status) return null;
  if (status.is_sample || status.fixtures_source === "SAMPLE") {
    return (
      <div className="border-b border-gold-500/30 bg-gold-500/10 px-4 py-2 text-center text-xs text-gold-400">
        <span className="inline-flex flex-wrap items-center justify-center gap-1.5">
          <Info className="h-3.5 w-3.5 shrink-0" />
          <span>
            <strong className="font-semibold">Demo:</strong> the WC26 fixture list shown here is
            illustrative until the official schedule is loaded.
          </span>
        </span>
      </div>
    );
  }
  return null;
}
