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
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      <div className="flex items-baseline justify-between mb-3 pb-2 border-b border-[#E2E8F0]">
        <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold">
          Collection Coverage
        </h4>
        <span className="text-[10px] font-mono text-[#64748B]">
          Multi-Tier Resolver Distribution
        </span>
      </div>

      {/* Proportional Segmented Bar */}
      <div className="h-3 w-full rounded-xs flex overflow-hidden bg-slate-100 mb-3">
        <div
          style={{ width: `${apiPct}%` }}
          className="bg-[#1E3A8A] transition-all"
          title={`API Direct: ${apiPct}% (${counts.api} quotes)`}
        />
        <div
          style={{ width: `${tariffPct}%` }}
          className="bg-[#0284C7] transition-all"
          title={`Tariff Sheets: ${tariffPct}% (${counts.tariff_sheet} quotes)`}
        />
        <div
          style={{ width: `${scrapePct}%` }}
          className="bg-[#93C5FD] transition-all"
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
          <span className="h-2 w-2 rounded-xs bg-[#1E3A8A] shrink-0" />
          <span className="text-[#64748B]">API</span>
          <span className="font-semibold text-[#0F172A] ml-auto">{apiPct}%</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-xs bg-[#0284C7] shrink-0" />
          <span className="text-[#64748B]">Tariff Sheet</span>
          <span className="font-semibold text-[#0F172A] ml-auto">{tariffPct}%</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-xs bg-[#93C5FD] shrink-0" />
          <span className="text-[#64748B]">Web Extract</span>
          <span className="font-semibold text-[#0F172A] ml-auto">{scrapePct}%</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-xs bg-amber-400 shrink-0" />
          <span className="text-[#64748B]">Simulation</span>
          <span className="font-semibold text-[#0F172A] ml-auto">{simPct}%</span>
        </div>
      </div>
    </div>
  );
}
