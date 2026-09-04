import React from "react";
import { formatINR } from "@/lib/formatters/currency";

interface MarketSnapshotProps {
  averageFare: number | null;
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
        Market Snapshot
      </h4>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Average Fare */}
        <div className="flex flex-col">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#626863]">
            Average Fare
          </span>
          <span className="font-serif text-2xl font-bold text-[#111716] tabular-nums mt-1">
            {formatINR(averageFare)}
          </span>
          <span className="text-[10px] text-[#626863] mt-0.5 font-sans">
            Observed consumer price
          </span>
        </div>

        {/* Quotes Collected */}
        <div className="flex flex-col">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#626863]">
            Quotes Collected
          </span>
          <span className="font-serif text-2xl font-bold text-[#111716] tabular-nums mt-1">
            {quotesCount}
          </span>
          <span className="text-[10px] text-[#626863] mt-0.5 font-sans">
            Daily price observations
          </span>
        </div>

        {/* Routes Covered */}
        <div className="flex flex-col">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#626863]">
            Routes Covered
          </span>
          <span className="font-serif text-2xl font-bold text-[#111716] tabular-nums mt-1">
            {routesCount} / 12
          </span>
          <span className="text-[10px] text-[#626863] mt-0.5 font-sans">
            DGCA domestic basket
          </span>
        </div>

        {/* Data Quality */}
        <div className="flex flex-col">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#626863]">
            Data Quality
          </span>
          <span className="font-serif text-2xl font-bold text-[#176B5B] tabular-nums mt-1">
            {qualityScore.toFixed(1)}%
          </span>
          <span className="text-[10px] text-[#626863] mt-0.5 font-sans">
            Clean & validated rate
          </span>
        </div>
      </div>
    </div>
  );
}
