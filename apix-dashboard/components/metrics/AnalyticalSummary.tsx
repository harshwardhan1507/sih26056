import React from "react";
import { formatINR } from "@/lib/formatters/currency";
import { formatPercent } from "@/lib/formatters/percentage";
import { ArrowUpRight, ArrowDownRight, TrendingUp } from "lucide-react";

interface AnalyticalSummaryProps {
  periodChange: number;
  timeframeLabel: string;
  highestDay: { change: number; date: string };
  lowestDay: { change: number; date: string };
  latestFare: number | null;
  className?: string;
}

export function AnalyticalSummary({
  periodChange,
  timeframeLabel,
  highestDay,
  lowestDay,
  latestFare,
  className = "",
}: AnalyticalSummaryProps) {
  return (
    <div
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#E2E8F0]">
        <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold flex items-center gap-1.5">
          <TrendingUp className="h-3.5 w-3.5 text-[#1E3A8A]" />
          Analytical Summary ({timeframeLabel})
        </h4>
        <span className="text-[10px] font-mono text-[#64748B]">
          Matched Fixed-Base Laspeyres Behavior
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Period Change */}
        <div className="flex flex-col">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#64748B]">
            Period Change
          </span>
          <div className="flex items-baseline gap-1 mt-1">
            <span
              className={`text-2xl font-bold tabular-nums ${
                periodChange > 0
                  ? "text-[#1D4ED8]"
                  : periodChange < 0
                  ? "text-[#DC2626]"
                  : "text-[#0F172A]"
              }`}
            >
              {formatPercent(periodChange)}
            </span>
          </div>
          <span className="text-[10px] text-[#64748B] mt-0.5">
            vs previous {timeframeLabel}
          </span>
        </div>

        {/* Highest Daily Increase */}
        <div className="flex flex-col">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#64748B]">
            Highest Daily Increase
          </span>
          <div className="flex items-center gap-1 mt-1 text-[#1D4ED8]">
            <ArrowUpRight className="h-4 w-4" />
            <span className="text-2xl font-bold tabular-nums">
              {formatPercent(highestDay.change)}
            </span>
          </div>
          <span className="text-[10px] text-[#64748B] mt-0.5 font-mono">
            {highestDay.date}
          </span>
        </div>

        {/* Lowest Daily Change */}
        <div className="flex flex-col">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#64748B]">
            Lowest Daily Change
          </span>
          <div className="flex items-center gap-1 mt-1 text-[#DC2626]">
            <ArrowDownRight className="h-4 w-4" />
            <span className="text-2xl font-bold tabular-nums">
              {formatPercent(lowestDay.change)}
            </span>
          </div>
          <span className="text-[10px] text-[#64748B] mt-0.5 font-mono">
            {lowestDay.date}
          </span>
        </div>

        {/* Average Fare */}
        <div className="flex flex-col">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[#64748B]">
            Average Observed Fare
          </span>
          <span className="text-2xl font-bold text-[#0F172A] tabular-nums mt-1">
            {formatINR(latestFare)}
          </span>
          <span className="text-[10px] text-[#64748B] mt-0.5">
            Latest observation period
          </span>
        </div>
      </div>
    </div>
  );
}
