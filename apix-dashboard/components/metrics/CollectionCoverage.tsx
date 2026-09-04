import React from "react";
import type { CollectionMethod } from "@/lib/api/types";

interface CollectionCoverageProps {
  byMethod?: Record<CollectionMethod, number>;
  totalQuotes?: number;
  className?: string;
}

export function CollectionCoverage({
  byMethod,
  totalQuotes = 300,
  className = "",
}: CollectionCoverageProps) {
  // Default distribution if byMethod not supplied
  const counts = byMethod || {
    api: 126,
    tariff_sheet: 93,
    scrape: 54,
    simulated: 27,
  };

  const total = totalQuotes > 0 ? totalQuotes : 300;

  const apiPct = Math.round((counts.api / total) * 100);
  const tariffPct = Math.round((counts.tariff_sheet / total) * 100);
  const scrapePct = Math.round((counts.scrape / total) * 100);
  const simPct = Math.max(0, 100 - apiPct - tariffPct - scrapePct);

  return (
    <div
      className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-4 ${className}`}
    >
      <div className="flex items-baseline justify-between mb-3 pb-2 border-b border-[#D8D7D0]">
        <h4 className="font-mono text-xs uppercase tracking-widest text-[#111716] font-semibold">
          Collection Coverage
        </h4>
        <span className="text-[10px] font-mono text-[#626863]">
          Multi-Tier Resolver Distribution
        </span>
      </div>

      {/* Proportional Segmented Bar */}
      <div className="h-3 w-full rounded-xs flex overflow-hidden bg-[#D8D7D0]/40 mb-3">
        <div
          style={{ width: `${apiPct}%` }}
          className="bg-[#176B5B] transition-all"
          title={`API Direct: ${apiPct}% (${counts.api} quotes)`}
        />
        <div
          style={{ width: `${tariffPct}%` }}
          className="bg-[#626863] transition-all"
          title={`Tariff Sheets: ${tariffPct}% (${counts.tariff_sheet} quotes)`}
        />
        <div
          style={{ width: `${scrapePct}%` }}
          className="bg-[#A9C4B8] transition-all"
          title={`Web Extraction: ${scrapePct}% (${counts.scrape} quotes)`}
        />
        <div
          style={{ width: `${simPct}%` }}
          className="bg-amber-400 transition-all"
          title={`Simulation Fallback: ${simPct}% (${counts.simulated} quotes)`}
        />
      </div>

      {/* Legend & Breakdown */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-xs bg-[#176B5B] shrink-0" />
          <span className="text-[#626863]">API</span>
          <span className="font-semibold text-[#111716] ml-auto">{apiPct}%</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-xs bg-[#626863] shrink-0" />
          <span className="text-[#626863]">Tariff Sheet</span>
          <span className="font-semibold text-[#111716] ml-auto">{tariffPct}%</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-xs bg-[#A9C4B8] shrink-0" />
          <span className="text-[#626863]">Web Extract</span>
          <span className="font-semibold text-[#111716] ml-auto">{scrapePct}%</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-xs bg-amber-400 shrink-0" />
          <span className="text-[#626863]">Simulation</span>
          <span className="font-semibold text-[#111716] ml-auto">{simPct}%</span>
        </div>
      </div>
    </div>
  );
}
