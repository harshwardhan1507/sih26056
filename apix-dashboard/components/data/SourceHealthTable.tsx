import React from "react";
import type { SourceStatusItem } from "@/lib/api/types";
import { formatUTCtoIST } from "@/lib/formatters/dates";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Radio, Clock } from "lucide-react";

interface SourceHealthTableProps {
  sources: SourceStatusItem[];
  className?: string;
}

export function SourceHealthTable({
  sources,
  className = "",
}: SourceHealthTableProps) {
  return (
    <div
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#E2E8F0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold flex items-center gap-1.5">
            <Radio className="h-3.5 w-3.5 text-[#1E3A8A]" />
            Multi-Tier Resolver Health Matrix
          </h4>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Contribution to the served dataset per adapter. Success rate and latency
            show a dash where they are not measured rather than an estimate.
          </p>
        </div>
        <span className="text-[10px] font-mono text-[#64748B]">
          {sources.length} Ingestion Feeds
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#E2E8F0] text-[10px] font-mono text-[#64748B] uppercase tracking-wider bg-slate-50/70">
              <th className="py-2.5 px-3 font-semibold">Data Source / Provider</th>
              <th className="py-2.5 px-3 font-semibold">Tier / Method</th>
              <th className="py-2.5 px-3 font-semibold">Status</th>
              <th className="py-2.5 px-3 font-semibold">Quotes</th>
              <th className="py-2.5 px-3 font-semibold">Share</th>
              <th className="py-2.5 px-3 font-semibold">Success Rate</th>
              <th className="py-2.5 px-3 font-semibold">Latency</th>
              <th className="py-2.5 px-3 font-semibold text-right">Last Check (IST)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0] font-sans">
            {sources.map((s) => (
              <tr key={s.source_id} className="hover:bg-slate-50 transition-colors">
                <td className="py-3 px-3">
                  <div className="font-mono font-bold text-xs text-[#0F172A]">
                    {s.name}
                  </div>
                  <div className="text-[10px] font-mono text-[#64748B]">
                    ID: {s.source_id}
                  </div>
                </td>

                <td className="py-3 px-3">
                  <StatusBadge type="method" value={s.type} size="sm" />
                </td>

                <td className="py-3 px-3">
                  <StatusBadge type="source" value={s.status} size="sm" />
                </td>

                <td className="py-3 px-3 font-mono text-xs tabular-nums text-[#0F172A]">
                  {typeof s.quotes_contributed === "number"
                    ? s.quotes_contributed.toLocaleString("en-IN")
                    : "—"}
                </td>

                <td className="py-3 px-3 font-mono text-xs tabular-nums text-[#64748B]">
                  {typeof s.share_pct === "number" ? `${s.share_pct.toFixed(1)}%` : "—"}
                </td>

                <td className="py-3 px-3 font-mono text-xs tabular-nums font-semibold text-[#0F172A]">
                  {s.success_rate === null || s.success_rate === undefined ? (
                    <span className="text-[#64748B]" title="Not measured">—</span>
                  ) : (
                    `${s.success_rate.toFixed(1)}%`
                  )}
                </td>

                <td className="py-3 px-3 font-mono text-xs tabular-nums text-[#64748B]">
                  {s.latency_ms === null || s.latency_ms === undefined ? (
                    <span title="Not measured">—</span>
                  ) : (
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-3 w-3 text-[#64748B]/60" />
                      <span>{s.latency_ms} ms</span>
                    </span>
                  )}
                </td>

                <td className="py-3 px-3 font-mono text-[11px] text-[#64748B] text-right">
                  {s.last_check_utc
                    ? formatUTCtoIST(s.last_check_utc, { format: "time" })
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
