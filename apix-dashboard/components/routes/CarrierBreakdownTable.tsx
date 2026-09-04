import React from "react";
import type { CarrierFareItem } from "@/lib/api/types";
import { formatINR } from "@/lib/formatters/currency";
import { formatPercent, getMovementPolarity } from "@/lib/formatters/percentage";
import { ArrowUpRight, ArrowDownRight, Minus, AlertTriangle, HelpCircle, CheckCircle2 } from "lucide-react";

interface CarrierBreakdownTableProps {
  carriers: CarrierFareItem[];
  windowMeanFare?: number | null;
  className?: string;
}

export function CarrierBreakdownTable({
  carriers,
  windowMeanFare,
  className = "",
}: CarrierBreakdownTableProps) {
  if (!carriers || carriers.length === 0) {
    return (
      <div
        className={`border border-[#E2E8F0] bg-white rounded-sm p-6 text-center text-[#64748B] font-mono text-xs ${className}`}
      >
        No carrier observations recorded for this advance window.
      </div>
    );
  }

  return (
    <div
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#E2E8F0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold">
            Carrier Fare Distribution
          </h4>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Scheduled airlines operating on this domestic segment
          </p>
        </div>
        {windowMeanFare && (
          <span className="text-[11px] font-mono text-[#64748B]">
            Segment Mean: <strong className="text-[#0F172A]">{formatINR(windowMeanFare)}</strong>
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#E2E8F0] text-[10px] font-mono text-[#64748B] uppercase tracking-wider bg-slate-50/70">
              <th className="py-2.5 px-3 font-semibold">Carrier</th>
              <th className="py-2.5 px-3 font-semibold">Observed Fare</th>
              <th className="py-2.5 px-3 font-semibold">Period Δ</th>
              <th className="py-2.5 px-3 font-semibold">Dispersion vs Mean</th>
              <th className="py-2.5 px-3 font-semibold text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0] font-sans">
            {carriers.map((c) => {
              const polarity = getMovementPolarity(c.change_pct);
              const hasFare = c.fare !== null && c.fare !== undefined;
              const dispersionPct =
                hasFare && windowMeanFare && windowMeanFare > 0
                  ? (((c.fare! - windowMeanFare) / windowMeanFare) * 100).toFixed(1)
                  : null;

              return (
                <tr key={c.carrier} className="hover:bg-slate-50 transition-colors">
                  {/* Carrier Code & Name */}
                  <td className="py-2.5 px-3">
                    <div className="font-mono font-bold text-xs text-[#0F172A]">
                      {c.name}
                    </div>
                    <div className="text-[10px] font-mono text-[#64748B]">
                      IATA: {c.carrier}
                    </div>
                  </td>

                  {/* Observed Fare */}
                  <td className="py-2.5 px-3 font-bold text-sm tabular-nums text-[#0F172A]">
                    {formatINR(c.fare)}
                  </td>

                  {/* Period Change */}
                  <td className="py-2.5 px-3">
                    {c.change_pct !== null && c.change_pct !== undefined ? (
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
                        {formatPercent(c.change_pct)}
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono text-[#64748B]">—</span>
                    )}
                  </td>

                  {/* Dispersion vs Window Mean */}
                  <td className="py-2.5 px-3 font-mono text-xs tabular-nums text-[#64748B]">
                    {dispersionPct !== null ? (
                      Number(dispersionPct) > 0 ? (
                        <span className="text-[#DC2626]">+{dispersionPct}%</span>
                      ) : (
                        <span className="text-[#1D4ED8]">{dispersionPct}%</span>
                      )
                    ) : (
                      "—"
                    )}
                  </td>

                  {/* Status Indicator */}
                  <td className="py-2.5 px-3 text-right">
                    {c.status === "available" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#1E3A8A] bg-blue-50 border border-[#1E3A8A]/30 px-1.5 py-0.5 rounded-xs">
                        <CheckCircle2 className="h-3 w-3" />
                        <span>Active</span>
                      </span>
                    )}

                    {c.status === "outlier_excluded" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-amber-800 bg-amber-50 border border-amber-300 px-1.5 py-0.5 rounded-xs">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Outlier Excluded</span>
                      </span>
                    )}

                    {c.status === "unavailable" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#64748B] bg-slate-100 border border-slate-300 px-1.5 py-0.5 rounded-xs">
                        <HelpCircle className="h-3 w-3" />
                        <span>Unavailable</span>
                      </span>
                    )}
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
