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
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#E2E8F0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-[#1E3A8A]" />
            Recent Daily Collection Clock Runs
          </h4>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            30-day collection clock audit history across 12 routes, 5 windows, and 5 carriers (300 quotes/day)
          </p>
        </div>
        <span className="text-[10px] font-mono text-[#64748B]">
          Audit Trail: {runs.length} Snapshots
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#E2E8F0] text-[10px] font-mono text-[#64748B] uppercase tracking-wider bg-slate-50/70">
              <th className="py-2.5 px-3 font-semibold">Snapshot Date</th>
              <th className="py-2.5 px-3 font-semibold">Run ID</th>
              <th className="py-2.5 px-3 font-semibold">Total Quotes</th>
              <th className="py-2.5 px-3 font-semibold">Valid Clean</th>
              <th className="py-2.5 px-3 font-semibold">Outliers</th>
              <th className="py-2.5 px-3 font-semibold">Sold Out</th>
              <th className="py-2.5 px-3 font-semibold">Simulated</th>
              <th className="py-2.5 px-3 font-semibold text-right">Run Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0] font-sans">
            {runs.map((r) => {
              const cleanRate = ((r.valid / r.total) * 100).toFixed(1);
              return (
                <tr key={r.run_id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-2.5 px-3 font-mono font-bold text-xs text-[#0F172A]">
                    {r.date}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[11px] text-[#64748B]">
                    {r.run_id}
                  </td>
                  <td className="py-2.5 px-3 font-mono tabular-nums text-xs font-semibold text-[#0F172A]">
                    {r.total}
                  </td>
                  <td className="py-2.5 px-3 font-mono tabular-nums text-xs text-[#1E3A8A] font-semibold">
                    {r.valid} ({cleanRate}%)
                  </td>
                  <td className="py-2.5 px-3 font-mono tabular-nums text-xs text-amber-800">
                    {r.outliers}
                  </td>
                  <td className="py-2.5 px-3 font-mono tabular-nums text-xs text-rose-800">
                    {r.sold_out}
                  </td>
                  <td className="py-2.5 px-3 font-mono tabular-nums text-xs text-[#64748B]">
                    {r.simulated_count}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    {r.status === "ok" ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[#1E3A8A] bg-blue-50 border border-[#1E3A8A]/30 px-2 py-0.5 rounded-xs font-semibold">
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
