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
      const aVal = a[sortField] ?? 0;
      const bVal = b[sortField] ?? 0;
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDir === "desc" ? bVal - aVal : aVal - bVal;
      }
      return 0;
    });

    return result;
  }, [routes, selectedHub, searchTerm, sortField, sortDir]);

  return (
    <div
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 shadow-xs ${className}`}
    >
      {/* Table Controls: Search & Hub Pills */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 mb-4 border-b border-[#E2E8F0]">
        {/* Hub Filter Pills */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0 font-mono text-xs">
          <span className="text-[10px] text-[#64748B] uppercase mr-1">Hub:</span>
          {HUBS.map((hub) => (
            <button
              key={hub}
              type="button"
              onClick={() => setSelectedHub(hub)}
              className={`px-2 py-0.5 rounded text-xs transition-colors cursor-pointer ${
                selectedHub === hub
                  ? "bg-[#1E3A8A] text-white font-semibold"
                  : "text-[#64748B] hover:bg-slate-100 hover:text-[#0F172A]"
              }`}
            >
              {hub}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-56">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#64748B]" />
          <input
            type="text"
            placeholder="Search route or city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-50 border border-[#E2E8F0] rounded pl-8 pr-3 py-1.5 text-xs text-[#0F172A] placeholder-[#64748B]/60 focus:outline-none focus:border-[#1E3A8A] font-mono"
          />
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#E2E8F0] text-[10px] font-mono text-[#64748B] uppercase tracking-wider bg-slate-50/70">
              <th className="py-2.5 px-3 font-semibold">Route</th>
              <th
                onClick={() => handleSort("weight")}
                className="py-2.5 px-3 font-semibold cursor-pointer hover:text-[#0F172A] transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Weight (DGCA)</span>
                  {sortField === "weight" ? (
                    sortDir === "desc" ? (
                      <ArrowDown className="h-3 w-3 text-[#1E3A8A]" />
                    ) : (
                      <ArrowUp className="h-3 w-3 text-[#1E3A8A]" />
                    )
                  ) : (
                    <ArrowUpDown className="h-3 w-3 opacity-40" />
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort("current_index")}
                className="py-2.5 px-3 font-semibold cursor-pointer hover:text-[#0F172A] transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Route Index</span>
                  {sortField === "current_index" ? (
                    sortDir === "desc" ? (
                      <ArrowDown className="h-3 w-3 text-[#1E3A8A]" />
                    ) : (
                      <ArrowUp className="h-3 w-3 text-[#1E3A8A]" />
                    )
                  ) : (
                    <ArrowUpDown className="h-3 w-3 opacity-40" />
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort("change_pct")}
                className="py-2.5 px-3 font-semibold cursor-pointer hover:text-[#0F172A] transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Change (30D)</span>
                  {sortField === "change_pct" ? (
                    sortDir === "desc" ? (
                      <ArrowDown className="h-3 w-3 text-[#1E3A8A]" />
                    ) : (
                      <ArrowUp className="h-3 w-3 text-[#1E3A8A]" />
                    )
                  ) : (
                    <ArrowUpDown className="h-3 w-3 opacity-40" />
                  )}
                </div>
              </th>
              <th
                onClick={() => handleSort("average_fare")}
                className="py-2.5 px-3 font-semibold cursor-pointer hover:text-[#0F172A] transition-colors"
              >
                <div className="flex items-center gap-1">
                  <span>Avg Fare</span>
                  {sortField === "average_fare" ? (
                    sortDir === "desc" ? (
                      <ArrowDown className="h-3 w-3 text-[#1E3A8A]" />
                    ) : (
                      <ArrowUp className="h-3 w-3 text-[#1E3A8A]" />
                    )
                  ) : (
                    <ArrowUpDown className="h-3 w-3 opacity-40" />
                  )}
                </div>
              </th>
              <th className="py-2.5 px-3 font-semibold">Trend</th>
              <th className="py-2.5 px-3 font-semibold text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0] font-sans">
            {filteredAndSortedRoutes.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-[#64748B] font-mono text-xs">
                  No routes matching &quot;{searchTerm}&quot;
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
                        ? "bg-blue-50/60 border-l-2 border-[#1E3A8A]"
                        : "hover:bg-slate-50"
                    }`}
                  >
                    {/* Route IATA & City */}
                    <td className="py-3 px-3">
                      <div className="font-mono font-bold text-xs text-[#0F172A] group-hover:text-[#1E3A8A] transition-colors">
                        {r.origin} → {r.destination}
                      </div>
                      <div className="text-[11px] text-[#64748B]">
                        {r.origin_city} to {r.destination_city}
                      </div>
                    </td>

                    {/* DGCA Weight */}
                    <td className="py-3 px-3 font-mono tabular-nums text-xs text-[#0F172A]">
                      {(r.weight * 100).toFixed(1)}%
                    </td>

                    {/* Current Route Index */}
                    <td className="py-3 px-3 font-bold text-sm tabular-nums text-[#0F172A]">
                      {r.current_index !== null ? r.current_index.toFixed(1) : "—"}
                    </td>

                    {/* Period Movement */}
                    <td className="py-3 px-3">
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

                    {/* Average Fare */}
                    <td className="py-3 px-3 font-mono tabular-nums text-xs font-medium text-[#0F172A]">
                      {formatINR(r.average_fare)}
                    </td>

                    {/* Sparkline */}
                    <td className="py-3 px-3">
                      <Sparkline
                        data={r.sparkline}
                        color={polarity === "positive" ? "#1D4ED8" : polarity === "negative" ? "#DC2626" : "#1E3A8A"}
                      />
                    </td>

                    {/* Details Link */}
                    <td className="py-3 px-3 text-right">
                      <Link
                        href={`/routes/${r.route_id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-[11px] font-mono text-[#1E3A8A] hover:underline font-medium"
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
