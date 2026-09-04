import React from "react";
import type { CollectionRunRecord } from "@/lib/api/types";
import { CheckCircle2, AlertTriangle, Calendar } from "lucide-react";

interface CollectionRunsTableProps {
  runs: CollectionRunRecord[];
  className?: string;
}

export function CollectionRunsTable({
  runs,
  className = "",
}: CollectionRunsTableProps) {
  return (
    <div
      className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-4 ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#D8D7D0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#111716] font-semibold flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-[#176B5B]" />
            Recent Daily Collection Clock Runs
          </h4>
          <p className="text-[11px] text-[#626863] mt-0.5">
            30-day collection clock audit history across 12 routes, 5 windows, and 5 carriers (300 quotes/day)
          </p>
        </div>
        <span className="text-[10px] font-mono text-[#626863]">
          Audit Trail: {runs.length} Snapshots
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#D8D7D0] text-[10px] font-mono text-[#626863] uppercase tracking-wider">
              <th className="py-2 px-2 font-semibold">Snapshot Date</th>
              <th className="py-2 px-2 font-semibold">Run ID</th>
              <th className="py-2 px-2 font-semibold">Total Quotes</th>
              <th className="py-2 px-2 font-semibold">Valid Clean</th>
              <th className="py-2 px-2 font-semibold">Outliers</th>
              <th className="py-2 px-2 font-semibold">Sold Out</th>
              <th className="py-2 px-2 font-semibold">Simulated</th>
              <th className="py-2 px-2 font-semibold text-right">Run Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#D8D7D0]/60 font-sans">
            {runs.map((r) => {
              const cleanRate = ((r.valid / r.total) * 100).toFixed(1);
              return (
                <tr key={r.run_id} className="hover:bg-[#F4F2EC] transition-colors">
                  <td className="py-2.5 px-2 font-mono font-bold text-xs text-[#111716]">
                    {r.date}
                  </td>
                  <td className="py-2.5 px-2 font-mono text-[11px] text-[#626863]">
                    {r.run_id}
                  </td>
                  <td className="py-2.5 px-2 font-mono tabular-nums text-xs font-semibold text-[#111716]">
                    {r.total}
                  </td>
                  <td className="py-2.5 px-2 font-mono tabular-nums text-xs text-[#176B5B] font-semibold">
                    {r.valid} ({cleanRate}%)
                  </td>
                  <td className="py-2.5 px-2 font-mono tabular-nums text-xs text-amber-800">
                    {r.outliers}
                  </td>
                  <td className="py-2.5 px-2 font-mono tabular-nums text-xs text-rose-800">
                    {r.sold_out}
                  </td>
                  <td className="py-2.5 px-2 font-mono tabular-nums text-xs text-[#626863]">
                    {r.simulated_count}
                  </td>
                  <td className="py-2.5 px-2 text-right">
                    {r.status === "ok" ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#176B5B] bg-[#176B5B]/10 border border-[#176B5B]/30 px-2 py-0.5 rounded-xs font-semibold">
                        <CheckCircle2 className="h-3 w-3" />
                        <span>Valid Run</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-amber-800 bg-amber-50 border border-amber-300 px-2 py-0.5 rounded-xs font-semibold">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Warning</span>
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
