import React from "react";
import type { QualityFlag, CollectionMethod } from "@/lib/api/types";
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, RefreshCw } from "lucide-react";

interface StatusBadgeProps {
  type: "quality" | "source" | "coverage" | "method";
  value: string;
  className?: string;
  size?: "sm" | "md";
}

export function StatusBadge({
  type,
  value,
  className = "",
  size = "md",
}: StatusBadgeProps) {
  const sizeClasses = size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-xs";

  if (type === "quality") {
    const flag = value as QualityFlag;
    switch (flag) {
      case "ok":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-[#1E3A8A]/30 bg-blue-50 text-[#1E3A8A] ${sizeClasses} ${className}`}
          >
            <CheckCircle2 className="h-3 w-3" />
            <span>Valid</span>
          </span>
        );
      case "outlier":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-amber-300 bg-amber-50 text-amber-800 ${sizeClasses} ${className}`}
          >
            <AlertTriangle className="h-3 w-3" />
            <span>Outlier</span>
          </span>
        );
      case "sold_out":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-rose-300 bg-rose-50 text-rose-800 ${sizeClasses} ${className}`}
          >
            <XCircle className="h-3 w-3" />
            <span>Sold Out</span>
          </span>
        );
      case "missing":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-slate-300 bg-slate-100 text-[#64748B] ${sizeClasses} ${className}`}
          >
            <HelpCircle className="h-3 w-3" />
            <span>Missing</span>
          </span>
        );
      case "imputed":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-sky-300 bg-sky-50 text-sky-800 ${sizeClasses} ${className}`}
          >
            <RefreshCw className="h-3 w-3" />
            <span>Imputed</span>
          </span>
        );
    }
  }

  if (type === "source") {
    switch (value) {
      case "not_integrated":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-[#D8D7D0] bg-[#F4F2EC] text-[#626863] ${sizeClasses} ${className}`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[#A8A69C]" />
            <span>Not Integrated</span>
          </span>
        );
      case "active":
      case "available":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-[#1E3A8A]/30 bg-blue-50 text-[#1E3A8A] ${sizeClasses} ${className}`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[#1E3A8A]" />
            <span>Available</span>
          </span>
        );
      case "fallback":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-amber-300 bg-amber-50 text-amber-800 ${sizeClasses} ${className}`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
            <span>Fallback</span>
          </span>
        );
      case "degraded":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-orange-300 bg-orange-50 text-orange-800 ${sizeClasses} ${className}`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-orange-500" />
            <span>Degraded</span>
          </span>
        );
      case "failed":
        return (
          <span
            className={`inline-flex items-center gap-1 font-mono rounded-xs border border-rose-300 bg-rose-50 text-rose-800 ${sizeClasses} ${className}`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
            <span>Failed</span>
          </span>
        );
    }
  }

  if (type === "method") {
    const method = value as CollectionMethod;
    const labels: Record<CollectionMethod, string> = {
      api: "API Direct",
      tariff_sheet: "Tariff Sheet",
      scrape: "Web Scrape",
      historical_panel: "Historical Panel",
      simulated: "Simulated Fallback",
      imputed: "Imputed",
      unknown: "Unknown Provenance",
    };
    return (
      <span
        className={`inline-flex items-center font-mono rounded-xs border border-[#E2E8F0] bg-white text-[#0F172A] ${sizeClasses} ${className}`}
      >
        {labels[method] || value}
      </span>
    );
  }

  // Default fallback badge
  return (
    <span
      className={`inline-flex items-center font-mono rounded-xs border border-[#E2E8F0] bg-white text-[#64748B] ${sizeClasses} ${className}`}
    >
      {value}
    </span>
  );
}
