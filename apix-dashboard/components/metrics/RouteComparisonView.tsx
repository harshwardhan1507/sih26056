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
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#E2E8F0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold">
            Route Basket Comparison
          </h4>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            12 domestic trunk routes sorted by DGCA passenger-traffic weight
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#E2E8F0] text-[10px] font-mono text-[#64748B] uppercase bg-slate-50/70">
              <th className="py-2.5 px-3 font-semibold">Route</th>
              <th className="py-2.5 px-3 font-semibold">DGCA Weight</th>
              <th className="py-2.5 px-3 font-semibold">Route Index</th>
              <th className="py-2.5 px-3 font-semibold">Period Δ</th>
              <th className="py-2.5 px-3 font-semibold">Avg Fare</th>
              <th className="py-2.5 px-3 font-semibold text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0] font-sans">
            {sorted.map((r) => {
              const polarity = getMovementPolarity(r.change_pct);
              return (
                <tr
                  key={r.route_id}
                  className="hover:bg-slate-50 transition-colors group"
                >
                  <td className="py-2.5 px-3">
                    <div className="font-mono font-bold text-xs text-[#0F172A]">
                      {r.origin} → {r.destination}
                    </div>
                    <div className="text-[11px] text-[#64748B]">
                      {r.origin_city} to {r.destination_city}
                    </div>
                  </td>
                  <td className="py-2.5 px-3 font-mono tabular-nums text-xs text-[#0F172A]">
                    {(r.weight * 100).toFixed(2)}%
                  </td>
                  <td className="py-2.5 px-3 font-bold text-sm tabular-nums text-[#0F172A]">
                    {r.current_index ? r.current_index.toFixed(1) : "—"}
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-flex items-center gap-0.5 text-xs font-mono font-semibold ${
                        polarity === "positive"
                          ? "text-[#1D4ED8]"
                          : polarity === "negative"
                          ? "text-[#DC2626]"
                          : "text-[#64748B]"
                      }`}
                    >
                      {polarity === "positive" && <ArrowUpRight className="h-3.5 w-3.5" />}
                      {polarity === "negative" && <ArrowDownRight className="h-3.5 w-3.5" />}
                      {polarity === "neutral" && <Minus className="h-3.5 w-3.5" />}
                      {formatPercent(r.change_pct)}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono tabular-nums text-xs font-medium text-[#0F172A]">
                    {formatINR(r.average_fare)}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <Link
                      href={`/routes/${r.route_id}`}
                      className="inline-flex items-center gap-1 text-[11px] font-mono text-[#1E3A8A] hover:underline font-medium"
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
