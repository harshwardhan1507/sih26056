"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import type { RouteSnapshot } from "@/lib/api/types";
import { formatINR } from "@/lib/formatters/currency";
import { formatPercent, getMovementPolarity } from "@/lib/formatters/percentage";
import { Sparkline } from "@/components/charts/Sparkline";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Search,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

interface RouteTableProps {
  routes: RouteSnapshot[];
  onSelectRoute?: (routeId: string) => void;
  selectedRouteId?: string | null;
  className?: string;
}

type SortField = "weight" | "current_index" | "change_pct" | "average_fare";
type SortDirection = "asc" | "desc";

const HUBS = ["ALL", "DEL", "BOM", "BLR", "CCU", "MAA", "HYD", "GOI"] as const;

export function RouteTable({
  routes,
  onSelectRoute,
  selectedRouteId,
  className = "",
}: RouteTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedHub, setSelectedHub] = useState<string>("ALL");
  const [sortField, setSortField] = useState<SortField>("weight");
  const [sortDir, setSortDir] = useState<SortDirection>("desc");

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === "desc" ? "asc" : "desc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const filteredAndSortedRoutes = useMemo(() => {
    let result = [...routes];

    // Filter by Hub
    if (selectedHub !== "ALL") {
      result = result.filter(
        (r) => r.origin === selectedHub || r.destination === selectedHub
      );
    }

    // Filter by Search Query
    if (searchTerm.trim().length > 0) {
      const q = searchTerm.trim().toLowerCase();
      result = result.filter(
        (r) =>
          r.route_id.toLowerCase().includes(q) ||
          r.origin.toLowerCase().includes(q) ||
          r.destination.toLowerCase().includes(q) ||
          r.origin_city.toLowerCase().includes(q) ||
          r.destination_city.toLowerCase().includes(q)
      );
    }

    // Sort
    result.sort((a, b) => {
      let aVal = a[sortField] ?? 0;
      let bVal = b[sortField] ?? 0;
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDir === "desc" ? bVal - aVal : aVal - bVal;
      }
      return 0;
    });

    return result;
  }, [routes, selectedHub, searchTerm, sortField, sortDir]);

  return (
    <div
      className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-4 ${className}`}
    >
      {/* Table Controls: Search & Hub Pills */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 mb-4 border-b border-[#D8D7D0]">
        {/* Hub Filter Pills */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0 font-mono text-xs">
          <span className="text-[10px] text-[#626863] uppercase mr-1">Hub:</span>
          {HUBS.map((hub) => (
            <button
              key={hub}
              type="button"
              onClick={() => setSelectedHub(hub)}
              className={`px-2 py-1 rounded-xs transition-colors cursor-pointer text-xs ${
                selectedHub === hub
                  ? "bg-[#111716] text-[#FAF9F5] font-semibold"
                  : "text-[#626863] hover:bg-[#F4F2EC] hover:text-[#111716]"
              }`}
            >
              {hub}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#626863]" />
          <input
            type="text"
            placeholder="Search route or city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#F4F2EC] border border-[#D8D7D0] rounded-xs pl-8 pr-3 py-1.5 text-xs text-[#111716] placeholder-[#626863]/60 focus:outline-none focus:border-[#176B5B] font-mono"
          />
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#D8D7D0] text-[10px] font-mono text-[#626863] uppercase tracking-wider bg-[#FAF9F5]">
              <th className="py-2.5 px-3 font-semibold">Route</th>
              <th
                onClick={() => handleSort("weight")}
                className="py-2.5 px-3 font-semibold cursor-pointer hover:text-[#111716] transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>DGCA Weight</span>
                  {sortField === "weight" ? (
                    sortDir === "desc" ? (
                      <ArrowDown className="h-3 w-3 text-[#176B5B]" />
                    ) : (
                      <ArrowUp className="h-3 w-3 text-[#176B5B]" />
                    )
                  ) : (
                    <ArrowUpDown className="h-3 w-3 opacity-40" />
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort("current_index")}
                className="py-2.5 px-3 font-semibold cursor-pointer hover:text-[#111716] transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Route Index</span>
                  {sortField === "current_index" ? (
                    sortDir === "desc" ? (
                      <ArrowDown className="h-3 w-3 text-[#176B5B]" />
                    ) : (
                      <ArrowUp className="h-3 w-3 text-[#176B5B]" />
                    )
                  ) : (
                    <ArrowUpDown className="h-3 w-3 opacity-40" />
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort("change_pct")}
                className="py-2.5 px-3 font-semibold cursor-pointer hover:text-[#111716] transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Period Δ</span>
                  {sortField === "change_pct" ? (
                    sortDir === "desc" ? (
                      <ArrowDown className="h-3 w-3 text-[#176B5B]" />
                    ) : (
                      <ArrowUp className="h-3 w-3 text-[#176B5B]" />
                    )
                  ) : (
                    <ArrowUpDown className="h-3 w-3 opacity-40" />
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort("average_fare")}
                className="py-2.5 px-3 font-semibold cursor-pointer hover:text-[#111716] transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Avg Fare</span>
                  {sortField === "average_fare" ? (
                    sortDir === "desc" ? (
                      <ArrowDown className="h-3 w-3 text-[#176B5B]" />
                    ) : (
                      <ArrowUp className="h-3 w-3 text-[#176B5B]" />
                    )
                  ) : (
                    <ArrowUpDown className="h-3 w-3 opacity-40" />
                  )}
                </div>
              </th>
              <th className="py-2.5 px-3 font-semibold">Sample</th>
              <th className="py-2.5 px-3 font-semibold">Trend</th>
              <th className="py-2.5 px-3 font-semibold text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#D8D7D0]/60 font-sans">
            {filteredAndSortedRoutes.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-[#626863] font-mono text-xs">
                  No routes matching "{searchTerm}"
                </td>
              </tr>
            ) : (
              filteredAndSortedRoutes.map((r) => {
                const polarity = getMovementPolarity(r.change_pct);
                const isSelected = selectedRouteId === r.route_id;

                return (
                  <tr
                    key={r.route_id}
                    onClick={() => onSelectRoute && onSelectRoute(r.route_id)}
                    className={`transition-colors cursor-pointer group ${
                      isSelected
                        ? "bg-[#176B5B]/10 border-l-2 border-[#176B5B]"
                        : "hover:bg-[#F4F2EC]"
                    }`}
                  >
                    {/* Route IATA & City */}
                    <td className="py-3 px-3">
                      <div className="font-mono font-bold text-xs text-[#111716] group-hover:text-[#176B5B] transition-colors">
                        {r.origin} → {r.destination}
                      </div>
                      <div className="text-[11px] text-[#626863]">
                        {r.origin_city} to {r.destination_city}
                      </div>
                    </td>

                    {/* DGCA Weight */}
                    <td className="py-3 px-3 font-mono tabular-nums text-xs text-[#111716]">
                      {(r.weight * 100).toFixed(2)}%
                    </td>

                    {/* Current Route Index */}
                    <td className="py-3 px-3 font-serif font-bold text-sm tabular-nums text-[#111716]">
                      {r.current_index !== null ? r.current_index.toFixed(1) : "—"}
                    </td>

                    {/* Period Movement */}
                    <td className="py-3 px-3">
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

                    {/* Average Fare */}
                    <td className="py-3 px-3 font-mono tabular-nums text-xs font-medium text-[#111716]">
                      {formatINR(r.average_fare)}
                    </td>

                    {/* Sample Size & Coverage */}
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-1.5 font-mono text-[11px]">
                        {r.coverage_status === "complete" ? (
                          <span className="inline-flex items-center gap-1 text-[#176B5B]">
                            <CheckCircle2 className="h-3 w-3" />
                            <span>{r.matched_observations || 30} obs</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded-xs border border-amber-300">
                            <AlertCircle className="h-3 w-3" />
                            <span>{r.matched_observations || 18} obs (partial)</span>
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Sparkline */}
                    <td className="py-3 px-3">
                      <Sparkline
                        data={r.sparkline}
                        color={polarity === "positive" ? "#1C806B" : polarity === "negative" ? "#B54343" : "#176B5B"}
                      />
                    </td>

                    {/* Details Link */}
                    <td className="py-3 px-3 text-right">
                      <Link
                        href={`/routes/${r.route_id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-[11px] font-mono text-[#176B5B] hover:underline font-medium"
                      >
                        <span>View</span>
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
