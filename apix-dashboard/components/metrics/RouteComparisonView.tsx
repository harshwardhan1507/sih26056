import React from "react";
import Link from "next/link";
import type { RouteSnapshot } from "@/lib/api/types";
import { formatINR } from "@/lib/formatters/currency";
import { formatPercent, getMovementPolarity } from "@/lib/formatters/percentage";
import { ArrowUpRight, ArrowDownRight, Minus, ArrowRight } from "lucide-react";

interface RouteComparisonViewProps {
  routes: RouteSnapshot[];
  className?: string;
}

export function RouteComparisonView({
  routes,
  className = "",
}: RouteComparisonViewProps) {
  // Sort routes by weight descending (authoritative DGCA importance)
  const sorted = [...routes].sort((a, b) => b.weight - a.weight);

  return (
    <div
      className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-4 ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#D8D7D0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#111716] font-semibold">
            Route Basket Comparison
          </h4>
          <p className="text-[11px] text-[#626863] mt-0.5">
            12 domestic trunk routes sorted by DGCA passenger-traffic weight
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#D8D7D0] text-[10px] font-mono text-[#626863] uppercase">
              <th className="py-2 px-2 font-semibold">Route</th>
              <th className="py-2 px-2 font-semibold">DGCA Weight</th>
              <th className="py-2 px-2 font-semibold">Route Index</th>
              <th className="py-2 px-2 font-semibold">Period Δ</th>
              <th className="py-2 px-2 font-semibold">Avg Fare</th>
              <th className="py-2 px-2 font-semibold text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#D8D7D0]/60 font-sans">
            {sorted.map((r) => {
              const polarity = getMovementPolarity(r.change_pct);
              return (
                <tr
                  key={r.route_id}
                  className="hover:bg-[#F4F2EC] transition-colors group"
                >
                  <td className="py-2.5 px-2">
                    <div className="font-mono font-bold text-xs text-[#111716]">
                      {r.origin} → {r.destination}
                    </div>
                    <div className="text-[11px] text-[#626863]">
                      {r.origin_city} to {r.destination_city}
                    </div>
                  </td>
                  <td className="py-2.5 px-2 font-mono tabular-nums text-xs">
                    {(r.weight * 100).toFixed(2)}%
                  </td>
                  <td className="py-2.5 px-2 font-serif font-bold text-sm tabular-nums text-[#111716]">
                    {r.current_index ? r.current_index.toFixed(1) : "—"}
                  </td>
                  <td className="py-2.5 px-2">
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
                      {formatPercent(r.change_pct)}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 font-mono tabular-nums text-xs font-medium text-[#111716]">
                    {formatINR(r.average_fare)}
                  </td>
                  <td className="py-2.5 px-2 text-right">
                    <Link
                      href={`/routes/${r.route_id}`}
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-[#176B5B] hover:underline font-medium"
                    >
                      <span>Detail</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
