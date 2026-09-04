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
        className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-6 text-center text-[#626863] font-mono text-xs ${className}`}
      >
        No carrier observations recorded for this advance window.
      </div>
    );
  }

  return (
    <div
      className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-4 ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#D8D7D0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#111716] font-semibold">
            Carrier Fare Distribution
          </h4>
          <p className="text-[11px] text-[#626863] mt-0.5">
            Scheduled airlines operating on this domestic segment
          </p>
        </div>
        {windowMeanFare && (
          <span className="text-[11px] font-mono text-[#626863]">
            Segment Mean: <strong className="text-[#111716]">{formatINR(windowMeanFare)}</strong>
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#D8D7D0] text-[10px] font-mono text-[#626863] uppercase tracking-wider">
              <th className="py-2 px-2 font-semibold">Carrier</th>
              <th className="py-2 px-2 font-semibold">Observed Fare</th>
              <th className="py-2 px-2 font-semibold">Period Δ</th>
              <th className="py-2 px-2 font-semibold">Dispersion vs Mean</th>
              <th className="py-2 px-2 font-semibold text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#D8D7D0]/60 font-sans">
            {carriers.map((c) => {
              const polarity = getMovementPolarity(c.change_pct);
              const hasFare = c.fare !== null && c.fare !== undefined;
              const dispersionPct =
                hasFare && windowMeanFare && windowMeanFare > 0
                  ? (((c.fare! - windowMeanFare) / windowMeanFare) * 100).toFixed(1)
                  : null;

              return (
                <tr key={c.carrier} className="hover:bg-[#F4F2EC] transition-colors">
                  {/* Carrier Code & Name */}
                  <td className="py-2.5 px-2">
                    <div className="font-mono font-bold text-xs text-[#111716]">
                      {c.name}
                    </div>
                    <div className="text-[10px] font-mono text-[#626863]">
                      IATA: {c.carrier}
                    </div>
                  </td>

                  {/* Observed Fare */}
                  <td className="py-2.5 px-2 font-serif font-bold text-sm tabular-nums text-[#111716]">
                    {formatINR(c.fare)}
                  </td>

                  {/* Period Change */}
                  <td className="py-2.5 px-2">
                    {c.change_pct !== null && c.change_pct !== undefined ? (
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
                        {formatPercent(c.change_pct)}
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono text-[#626863]">—</span>
                    )}
                  </td>

                  {/* Dispersion vs Window Mean */}
                  <td className="py-2.5 px-2 font-mono text-xs tabular-nums text-[#626863]">
                    {dispersionPct !== null ? (
                      Number(dispersionPct) > 0 ? (
                        <span className="text-[#B54343]">+{dispersionPct}%</span>
                      ) : (
                        <span className="text-[#1C806B]">{dispersionPct}%</span>
                      )
                    ) : (
                      "—"
                    )}
                  </td>

                  {/* Status Indicator */}
                  <td className="py-2.5 px-2 text-right">
                    {c.status === "available" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#176B5B] bg-[#176B5B]/10 border border-[#176B5B]/30 px-1.5 py-0.5 rounded-xs">
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
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#626863] bg-stone-100 border border-stone-300 px-1.5 py-0.5 rounded-xs">
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
