import React from "react";
import Link from "next/link";
import type { RouteSnapshot } from "@/lib/api/types";
import { formatPercent, getMovementPolarity } from "@/lib/formatters/percentage";
import { ArrowUpRight, ArrowDownRight, Minus, ArrowRight } from "lucide-react";

interface TopMoversProps {
  routes: RouteSnapshot[];
  limit?: number;
  className?: string;
}

export function TopMovers({
  routes,
  limit = 5,
  className = "",
}: TopMoversProps) {
  // Sort by absolute change percentage descending to show top drivers
  const sorted = [...routes].sort((a, b) => {
    const aChg = Math.abs(a.change_pct ?? 0);
    const bChg = Math.abs(b.change_pct ?? 0);
    return bChg - aChg;
  });

  const movers = sorted.slice(0, limit);

  return (
    <div className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-4 ${className}`}>
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#D8D7D0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#111716] font-semibold">
            What's Driving the Index
          </h4>
          <p className="text-[11px] text-[#626863] mt-0.5">
            Top moving routes weighted by DGCA passenger traffic
          </p>
        </div>

        <Link
          href="/routes"
          className="inline-flex items-center gap-1 text-[11px] font-mono text-[#176B5B] hover:underline font-medium"
        >
          <span>All 12 routes</span>
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      <div className="divide-y divide-[#D8D7D0]/60">
        {movers.map((route) => {
          const polarity = getMovementPolarity(route.change_pct);
          const weightPct = (route.weight * 100).toFixed(1);

          return (
            <Link
              key={route.route_id}
              href={`/routes/${route.route_id}`}
              className="flex items-center justify-between py-2.5 px-2 hover:bg-[#F4F2EC] rounded-xs transition-colors group"
            >
              <div className="flex items-baseline gap-2">
                <span className="font-mono font-bold text-xs text-[#111716] group-hover:text-[#176B5B] transition-colors">
                  {route.origin} → {route.destination}
                </span>
                <span className="text-[11px] text-[#626863] font-sans">
                  {route.origin_city} to {route.destination_city}
                </span>
                <span className="text-[10px] font-mono text-[#626863]/80 bg-[#D8D7D0]/40 px-1.5 py-0.2 rounded-xs ml-1">
                  {weightPct}% weight
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center gap-0.5 text-xs font-mono font-semibold ${
                    polarity === "positive"
                      ? "text-[#1C806B]"
                      : polarity === "negative"
                      ? "text-[#B54343]"
                      : "text-[#626863]"
                  }`}
                >
                  {polarity === "positive" && <ArrowUpRight className="h-3.5 w-3.5" />}
                  {polarity === "negative" && <ArrowDownRight className="h-3.5 w-3.5" />}
                  {polarity === "neutral" && <Minus className="h-3.5 w-3.5" />}
                  {formatPercent(route.change_pct)}
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
