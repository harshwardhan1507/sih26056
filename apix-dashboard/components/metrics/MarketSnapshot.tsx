import React from "react";
import { formatINR } from "@/lib/formatters/currency";
import { IndianRupee, Layers, CheckCircle2, ShieldCheck } from "lucide-react";

interface MarketSnapshotProps {
  averageFare: number;
  quotesCount: number;
  routesCount: number;
  qualityScore: number;
  className?: string;
}

export function MarketSnapshot({
  averageFare,
  quotesCount,
  routesCount,
  qualityScore,
  className = "",
}: MarketSnapshotProps) {
  return (
    <div
      className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-4 ${className}`}
    >
      <h4 className="font-mono text-xs uppercase tracking-widest text-[#111716] font-semibold mb-4 pb-2 border-b border-[#D8D7D0]">
        Market Snapshot (Today)
      </h4>

      <div className="grid grid-cols-2 sm:grid-cols-2 gap-4">
        {/* Average Fare */}
        <div className="flex items-start gap-3 p-3 bg-[#F4F2EC] rounded border border-[#D8D7D0]/60">
          <div className="p-2 bg-[#162923] text-emerald-300 rounded shrink-0 mt-0.5">
            <IndianRupee className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#626863] block">
              Avg. Fare (One-Way)
            </span>
            <span className="font-serif text-2xl font-bold text-[#111716] tabular-nums mt-0.5 block">
              {formatINR(averageFare)}
            </span>
            <span className="text-[10px] text-[#626863] font-sans">
              Weighted basket mean
            </span>
          </div>
        </div>

        {/* Quotes Collected */}
        <div className="flex items-start gap-3 p-3 bg-[#F4F2EC] rounded border border-[#D8D7D0]/60">
          <div className="p-2 bg-[#162923] text-emerald-300 rounded shrink-0 mt-0.5">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#626863] block">
              Quotes Collected
            </span>
            <span className="font-serif text-2xl font-bold text-[#111716] tabular-nums mt-0.5 block">
              {quotesCount}
            </span>
            <span className="text-[10px] text-[#626863] font-sans">
              12 routes × 5 windows × 5 carriers
            </span>
          </div>
        </div>

        {/* Routes Covered */}
        <div className="flex items-start gap-3 p-3 bg-[#F4F2EC] rounded border border-[#D8D7D0]/60">
          <div className="p-2 bg-[#162923] text-emerald-300 rounded shrink-0 mt-0.5">
            <CheckCircle2 className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#626863] block">
              Routes Covered
            </span>
            <span className="font-serif text-2xl font-bold text-[#111716] tabular-nums mt-0.5 block">
              {routesCount} / 12
            </span>
            <span className="text-[10px] text-[#626863] font-sans">
              100% DGCA basket active
            </span>
          </div>
        </div>

        {/* Data Quality */}
        <div className="flex items-start gap-3 p-3 bg-[#F4F2EC] rounded border border-[#D8D7D0]/60">
          <div className="p-2 bg-[#162923] text-emerald-300 rounded shrink-0 mt-0.5">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#626863] block">
              Data Quality Score
            </span>
            <span className="font-serif text-2xl font-bold text-[#176B5B] tabular-nums mt-0.5 block">
              {qualityScore.toFixed(1)}%
            </span>
            <span className="text-[10px] text-[#626863] font-sans">
              Clean & validated rate
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
