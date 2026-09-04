import React from "react";
import { formatINR } from "@/lib/formatters/currency";
import { IndianRupee, Layers, CheckCircle2, ShieldCheck } from "lucide-react";

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
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold mb-4 pb-2 border-b border-[#E2E8F0]">
        Market Snapshot (Today)
      </h4>

      <div className="grid grid-cols-2 sm:grid-cols-2 gap-4">
        {/* Average Fare */}
        <div className="flex items-start gap-3 p-3 bg-slate-50 rounded border border-[#E2E8F0]">
          <div className="p-2 bg-[#0B1E36] text-sky-300 rounded shrink-0 mt-0.5">
            <IndianRupee className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#64748B] block">
              Avg. Fare (One-Way)
            </span>
            <span className="text-2xl font-bold text-[#0F172A] tabular-nums mt-0.5 block">
              {formatINR(averageFare)}
            </span>
            <span className="text-[10px] text-[#64748B] font-sans">
              Weighted basket mean
            </span>
          </div>
        </div>

        {/* Quotes Collected */}
        <div className="flex items-start gap-3 p-3 bg-slate-50 rounded border border-[#E2E8F0]">
          <div className="p-2 bg-[#0B1E36] text-sky-300 rounded shrink-0 mt-0.5">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#64748B] block">
              Quotes Collected
            </span>
            <span className="text-2xl font-bold text-[#0F172A] tabular-nums mt-0.5 block">
              {quotesCount}
            </span>
            <span className="text-[10px] text-[#64748B] font-sans">
              12 routes × 5 windows × 5 carriers
            </span>
          </div>
        </div>

        {/* Routes Covered */}
        <div className="flex items-start gap-3 p-3 bg-slate-50 rounded border border-[#E2E8F0]">
          <div className="p-2 bg-[#0B1E36] text-sky-300 rounded shrink-0 mt-0.5">
            <CheckCircle2 className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#64748B] block">
              Routes Covered
            </span>
            <span className="text-2xl font-bold text-[#0F172A] tabular-nums mt-0.5 block">
              {routesCount} / 12
            </span>
            <span className="text-[10px] text-[#64748B] font-sans">
              100% DGCA basket active
            </span>
          </div>
        </div>

        {/* Data Quality */}
        <div className="flex items-start gap-3 p-3 bg-slate-50 rounded border border-[#E2E8F0]">
          <div className="p-2 bg-[#0B1E36] text-sky-300 rounded shrink-0 mt-0.5">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#64748B] block">
              Data Quality Score
            </span>
            <span className="text-2xl font-bold text-[#1E3A8A] tabular-nums mt-0.5 block">
              {qualityScore.toFixed(1)}%
            </span>
            <span className="text-[10px] text-[#64748B] font-sans">
              Clean & validated rate
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
