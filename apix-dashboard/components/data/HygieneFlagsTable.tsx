import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, RefreshCw } from "lucide-react";

interface FlagDetail {
  flag: string;
  name: string;
  count: number;
  sharePct: number;
  treatment: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  colorClass: string;
}

interface HygieneFlagsTableProps {
  counts: {
    ok: number;
    outlier: number;
    sold_out: number;
    missing: number;
    imputed: number;
  };
  total: number;
  className?: string;
}

export function HygieneFlagsTable({
  counts,
  total,
  className = "",
}: HygieneFlagsTableProps) {
  const flags: FlagDetail[] = [
    {
      flag: "ok",
      name: "Valid Observation",
      count: counts.ok,
      sharePct: total > 0 ? (counts.ok / total) * 100 : 0,
      treatment: "Included in Jevons",
      description: "Clean fare observation verified within schema bounds and outlier fences. Enters geometric mean price relative.",
      icon: CheckCircle2,
      colorClass: "text-[#1E3A8A] bg-blue-50 border-[#1E3A8A]/30",
    },
    {
      flag: "outlier",
      name: "Price Outlier",
      count: counts.outlier,
      sharePct: total > 0 ? (counts.outlier / total) * 100 : 0,
      treatment: "Excluded from Relative",
      description: "Fare exceeds 3.0x IQR upper fence for (route, window) market cell. Isolated to prevent spurious volatility spikes.",
      icon: AlertTriangle,
      colorClass: "text-amber-800 bg-amber-50 border-amber-300",
    },
    {
      flag: "sold_out",
      name: "Sold-Out Flight",
      count: counts.sold_out,
      sharePct: total > 0 ? (counts.sold_out / total) * 100 : 0,
      treatment: "Missing Value (Fare = null)",
      description: "Flight unavailable at observation time. Strictly recorded with total_fare_inr = null, NEVER zero. Drops from matched pair.",
      icon: XCircle,
      colorClass: "text-rose-800 bg-rose-50 border-rose-300",
    },
    {
      flag: "missing",
      name: "Missing Quote",
      count: counts.missing,
      sharePct: total > 0 ? (counts.missing / total) * 100 : 0,
      treatment: "Unobserved Carrier Cell",
      description: "Carrier not scheduling flights on this city-pair/horizon during collection cycle.",
      icon: HelpCircle,
      colorClass: "text-slate-800 bg-slate-100 border-slate-300",
    },
    {
      flag: "imputed",
      name: "Imputed Value",
      count: counts.imputed,
      sharePct: total > 0 ? (counts.imputed / total) * 100 : 0,
      treatment: "Transparent Flagging",
      description: "Statistical imputation applied. Zero synthetic imputation injected in official series without MoSPI PSD flag.",
      icon: RefreshCw,
      colorClass: "text-sky-800 bg-sky-50 border-sky-300",
    },
  ];

  return (
    <div
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      <div className="pb-3 mb-3 border-b border-[#E2E8F0]">
        <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold">
          Data Quality Flag Specification & Treatment
        </h4>
        <p className="text-[11px] text-[#64748B] mt-0.5">
          Standardized handling rules for observations across collection, cleaning, and indexing
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#E2E8F0] text-[10px] font-mono text-[#64748B] uppercase tracking-wider bg-slate-50/70">
              <th className="py-2.5 px-3 font-semibold">Flag</th>
              <th className="py-2.5 px-3 font-semibold">Observations</th>
              <th className="py-2.5 px-3 font-semibold">Index Treatment</th>
              <th className="py-2.5 px-3 font-semibold">Hygiene Rationale</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0] font-sans">
            {flags.map((item) => {
              const Icon = item.icon;
              return (
                <tr key={item.flag} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-3">
                    <span
                      className={`inline-flex items-center gap-1 font-mono text-[11px] px-2 py-0.5 rounded-xs border font-medium ${item.colorClass}`}
                    >
                      <Icon className="h-3 w-3" />
                      <span>{item.name}</span>
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-xs tabular-nums text-[#0F172A]">
                    <span className="font-bold">{item.count}</span>
                    <span className="text-[#64748B] ml-1.5 text-[10px]">
                      ({item.sharePct.toFixed(1)}%)
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-xs font-semibold text-[#0F172A]">
                    {item.treatment}
                  </td>
                  <td className="py-3 px-3 text-xs text-[#64748B] leading-relaxed max-w-md">
                    {item.description}
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
