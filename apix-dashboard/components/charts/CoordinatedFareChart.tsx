"use client";

import React, { useState, useMemo, useCallback, useRef } from "react";
import type { IndexPoint } from "@/lib/api/types";
import { formatINR } from "@/lib/formatters/currency";
import { formatPercent } from "@/lib/formatters/percentage";
import { Tabs } from "@/components/common/Tabs";

interface CoordinatedFareChartProps {
  data: IndexPoint[];
  baseValue?: number;
  latestAverageFare?: number | null;
  timeframe: "7D" | "30D" | "90D";
  onTimeframeChange: (tf: "7D" | "30D" | "90D") => void;
  className?: string;
}

export function CoordinatedFareChart({
  data,
  baseValue = 100.0,
  // No default fare. A hardcoded INR 6,842 anchor drew a fare curve that
  // looked measured but was not; with no anchor the fare track is omitted.
  latestAverageFare = null,
  timeframe,
  onTimeframeChange,
  className = "",
}: CoordinatedFareChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // Filter series based on timeframe
  const points = useMemo(() => {
    if (!data || data.length === 0) return [];
    const limit = timeframe === "7D" ? 7 : timeframe === "30D" ? 30 : 90;
    return data.slice(-limit);
  }, [data, timeframe]);

  // Index-implied fare path, anchored on the latest observed average fare.
  // Without an anchor there is nothing to scale, so every fare is null and the
  // fare track renders empty rather than inventing a level.
  const pointsWithFare = useMemo(() => {
    const anchorIndex = points[points.length - 1]?.index_value;
    const canDeriveFare =
      latestAverageFare !== null &&
      latestAverageFare !== undefined &&
      anchorIndex !== null &&
      anchorIndex !== undefined &&
      anchorIndex > 0;

    return points.map((p) => {
      if (!canDeriveFare || p.index_value === null || p.index_value === undefined) {
        return { ...p, fare: null };
      }
      const baseFare = (latestAverageFare / anchorIndex) * baseValue;
      return { ...p, fare: Math.round(baseFare * (p.index_value / baseValue)) };
    });
  }, [points, baseValue, latestAverageFare]);

  // Top Chart (Index) valid values
  const validIndices = useMemo(() => {
    return pointsWithFare
      .map((p) => p.index_value)
      .filter((v): v is number => v !== null && v !== undefined && !Number.isNaN(v));
  }, [pointsWithFare]);

  // Bottom Chart (Fare) valid values
  const validFares = useMemo(() => {
    return pointsWithFare
      .map((p) => p.fare)
      .filter((v): v is number => v !== null && v !== undefined && !Number.isNaN(v));
  }, [pointsWithFare]);

  // Geometry
  const width = 800;
  const chartHeight = 180;
  const padLeft = 60;
  const padRight = 35;
  const padTop = 20;
  const padBottom = 25;

  const chartW = width - padLeft - padRight;
  const chartH = chartHeight - padTop - padBottom;

  // Scale: Top Chart (Index)
  const indexBounds = useMemo(() => {
    if (validIndices.length === 0) return { min: 95, max: 105, ticks: [95, 100, 105] };
    const rawMin = Math.min(...validIndices, baseValue);
    const rawMax = Math.max(...validIndices, baseValue);
    const pad = Math.max((rawMax - rawMin) * 0.15, 1.0);
    const min = Math.floor(rawMin - pad);
    const max = Math.ceil(rawMax + pad);
    const step = (max - min) / 3;
    return {
      min,
      max,
      ticks: [min, Number((min + step).toFixed(1)), Number((min + step * 2).toFixed(1)), max],
    };
  }, [validIndices, baseValue]);

  // Scale: Bottom Chart (Fare in INR)
  const fareBounds = useMemo(() => {
    if (validFares.length === 0) return { min: 6000, max: 8000, ticks: [6000, 7000, 8000] };
    const rawMin = Math.min(...validFares);
    const rawMax = Math.max(...validFares);
    const pad = Math.max((rawMax - rawMin) * 0.15, 150);
    const min = Math.floor((rawMin - pad) / 100) * 100;
    const max = Math.ceil((rawMax + pad) / 100) * 100;
    const step = Math.round((max - min) / 3);
    return {
      min,
      max,
      ticks: [min, min + step, min + step * 2, max],
    };
  }, [validFares]);

  // Shared horizontal scale
  const getX = useCallback(
    (index: number) => {
      if (pointsWithFare.length <= 1) return padLeft + chartW / 2;
      return padLeft + (index / (pointsWithFare.length - 1)) * chartW;
    },
    [chartW, padLeft, pointsWithFare.length]
  );

  // Top Chart Y scale
  const getIndexY = useCallback(
    (val: number) => {
      if (indexBounds.max === indexBounds.min) return padTop + chartH / 2;
      return padTop + chartH - ((val - indexBounds.min) / (indexBounds.max - indexBounds.min)) * chartH;
    },
    [chartH, indexBounds.max, indexBounds.min, padTop]
  );

  // Bottom Chart Y scale
  const getFareY = useCallback(
    (val: number) => {
      if (fareBounds.max === fareBounds.min) return padTop + chartH / 2;
      return padTop + chartH - ((val - fareBounds.min) / (fareBounds.max - fareBounds.min)) * chartH;
    },
    [chartH, fareBounds.max, fareBounds.min, padTop]
  );

  // Paths: Top Chart (Index)
  const indexPathSegments = useMemo(() => {
    const segments: string[] = [];
    let current: string[] = [];
    pointsWithFare.forEach((p, idx) => {
      if (p.index_value !== null && p.index_value !== undefined) {
        const x = getX(idx);
        const y = getIndexY(p.index_value);
        if (current.length === 0) current.push(`M ${x} ${y}`);
        else current.push(`L ${x} ${y}`);
      } else {
        if (current.length > 0) {
          segments.push(current.join(" "));
          current = [];
        }
      }
    });
    if (current.length > 0) segments.push(current.join(" "));
    return segments;
  }, [pointsWithFare, getX, getIndexY]);

  // Paths: Bottom Chart (Fare)
  const farePathSegments = useMemo(() => {
    const segments: string[] = [];
    let current: string[] = [];
    pointsWithFare.forEach((p, idx) => {
      if (p.fare !== null && p.fare !== undefined) {
        const x = getX(idx);
        const y = getFareY(p.fare);
        if (current.length === 0) current.push(`M ${x} ${y}`);
        else current.push(`L ${x} ${y}`);
      } else {
        if (current.length > 0) {
          segments.push(current.join(" "));
          current = [];
        }
      }
    });
    if (current.length > 0) segments.push(current.join(" "));
    return segments;
  }, [pointsWithFare, getX, getFareY]);

  // Mouse interaction
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current || pointsWithFare.length === 0) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const relX = (mouseX / rect.width) * width;

    if (relX < padLeft || relX > width - padRight) {
      setHoverIndex(null);
      return;
    }

    const ratio = (relX - padLeft) / chartW;
    const closest = Math.round(ratio * (pointsWithFare.length - 1));
    const clamped = Math.max(0, Math.min(pointsWithFare.length - 1, closest));
    setHoverIndex(clamped);
  };

  const activePoint = hoverIndex !== null ? pointsWithFare[hoverIndex] : null;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Timeframe Controls */}
      <div className="flex items-center justify-between">
        <div>
          <span className="font-mono text-xs uppercase tracking-wider text-[#0F172A] font-semibold">
            Coordinated Time Series Comparison
          </span>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Two vertically stacked aligned charts sharing a synchronized timeline. Never dual-axis.
          </p>
        </div>

        <Tabs
          size="sm"
          tabs={[
            { id: "7D", label: "7D" },
            { id: "30D", label: "30D" },
            { id: "90D", label: "90D" },
          ]}
          activeTab={timeframe}
          onChange={onTimeframeChange}
        />
      </div>

      {/* Synchronized Container */}
      <div
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoverIndex(null)}
        className="relative border border-[#E2E8F0] bg-white rounded-sm p-4 cursor-crosshair select-none space-y-3 shadow-xs"
      >
        {/* CHART 1: Index Series (Top) */}
        <div>
          <div className="flex items-center justify-between mb-1 px-2">
            <span className="text-[11px] font-mono font-semibold text-[#1E3A8A] uppercase tracking-wider flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-xs bg-[#1E3A8A]" />
              APIx Laspeyres Index Series (Base = 100.0)
            </span>
            {activePoint && activePoint.index_value !== null && (
              <span className="text-xs font-mono font-bold text-[#1E3A8A] tabular-nums">
                {activePoint.index_value.toFixed(1)}
              </span>
            )}
          </div>

          <svg viewBox={`0 0 ${width} ${chartHeight}`} className="w-full h-auto overflow-visible">
            {/* Y Ticks */}
            {indexBounds.ticks.map((t) => {
              const y = getIndexY(t);
              const isBase = Math.abs(t - baseValue) < 0.05;
              return (
                <g key={t}>
                  <line
                    x1={padLeft}
                    y1={y}
                    x2={width - padRight}
                    y2={y}
                    stroke={isBase ? "#0F172A" : "#E2E8F0"}
                    strokeWidth={isBase ? 1 : 0.6}
                    strokeDasharray={isBase ? "4 3" : undefined}
                    opacity={isBase ? 0.7 : 0.8}
                  />
                  <text
                    x={padLeft - 8}
                    y={y + 3.5}
                    textAnchor="end"
                    className="text-[10px] font-mono fill-[#64748B] tabular-nums"
                  >
                    {t.toFixed(1)}
                  </text>
                </g>
              );
            })}

            {/* Path */}
            {indexPathSegments.map((d, i) => (
              <path
                key={i}
                d={d}
                fill="none"
                stroke="#1E3A8A"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ))}

            {/* Hover Indicator */}
            {hoverIndex !== null && activePoint && (
              <g>
                <line
                  x1={getX(hoverIndex)}
                  y1={padTop}
                  x2={getX(hoverIndex)}
                  y2={padTop + chartH}
                  stroke="#0F172A"
                  strokeWidth="1"
                  strokeDasharray="3 3"
                  opacity="0.5"
                />
                {activePoint.index_value !== null && (
                  <circle
                    cx={getX(hoverIndex)}
                    cy={getIndexY(activePoint.index_value)}
                    r="4.5"
                    fill="#FFFFFF"
                    stroke="#1E3A8A"
                    strokeWidth="2.5"
                  />
                )}
              </g>
            )}
          </svg>
        </div>

        {/* Divider rule between stacked charts */}
        <div className="border-t border-[#E2E8F0] mx-2" />

        {/* CHART 2: Observed Average Fare (Bottom) */}
        <div>
          <div className="flex items-center justify-between mb-1 px-2">
            <span className="text-[11px] font-mono font-semibold text-[#0F172A] uppercase tracking-wider flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-xs bg-[#0F172A]" />
              Observed Average Consumer Fare (INR ₹)
            </span>
            {activePoint && activePoint.fare !== null && (
              <span className="text-xs font-mono font-bold text-[#0F172A] tabular-nums">
                {formatINR(activePoint.fare)}
              </span>
            )}
          </div>

          <svg viewBox={`0 0 ${width} ${chartHeight}`} className="w-full h-auto overflow-visible">
            {/* Y Ticks */}
            {fareBounds.ticks.map((t) => {
              const y = getFareY(t);
              return (
                <g key={t}>
                  <line
                    x1={padLeft}
                    y1={y}
                    x2={width - padRight}
                    y2={y}
                    stroke="#E2E8F0"
                    strokeWidth="0.6"
                    opacity="0.8"
                  />
                  <text
                    x={padLeft - 8}
                    y={y + 3.5}
                    textAnchor="end"
                    className="text-[10px] font-mono fill-[#64748B] tabular-nums"
                  >
                    ₹{t.toLocaleString("en-IN")}
                  </text>
                </g>
              );
            })}

            {/* Path */}
            {farePathSegments.map((d, i) => (
              <path
                key={i}
                d={d}
                fill="none"
                stroke="#0F172A"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ))}

            {/* Hover Indicator */}
            {hoverIndex !== null && activePoint && (
              <g>
                <line
                  x1={getX(hoverIndex)}
                  y1={padTop}
                  x2={getX(hoverIndex)}
                  y2={padTop + chartH}
                  stroke="#0F172A"
                  strokeWidth="1"
                  strokeDasharray="3 3"
                  opacity="0.5"
                />
                {activePoint.fare !== null && (
                  <circle
                    cx={getX(hoverIndex)}
                    cy={getFareY(activePoint.fare)}
                    r="4.5"
                    fill="#FFFFFF"
                    stroke="#0F172A"
                    strokeWidth="2.5"
                  />
                )}
              </g>
            )}

            {/* Shared X-Axis Dates at the bottom */}
            {pointsWithFare.length > 1 && (
              <>
                <text
                  x={padLeft}
                  y={chartHeight - 4}
                  textAnchor="start"
                  className="text-[10px] font-mono fill-[#64748B]"
                >
                  {pointsWithFare[0].date}
                </text>
                <text
                  x={padLeft + chartW / 2}
                  y={chartHeight - 4}
                  textAnchor="middle"
                  className="text-[10px] font-mono fill-[#64748B]"
                >
                  {pointsWithFare[Math.floor(pointsWithFare.length / 2)].date}
                </text>
                <text
                  x={width - padRight}
                  y={chartHeight - 4}
                  textAnchor="end"
                  className="text-[10px] font-mono fill-[#64748B]"
                >
                  {pointsWithFare[pointsWithFare.length - 1].date}
                </text>
              </>
            )}
          </svg>
        </div>

        {/* Hover Tooltip synchronizing both values */}
        {hoverIndex !== null && activePoint && (
          <div
            className="absolute z-20 pointer-events-none p-2.5 bg-[#0F172A] text-white text-xs font-mono rounded-xs shadow-lg"
            style={{
              left: `${(getX(hoverIndex) / width) * 100}%`,
              top: "14px",
              transform: "translateX(-50%)",
            }}
          >
            <div className="text-[10px] text-slate-300 border-b border-slate-700 pb-1 mb-1">
              {activePoint.date} (Day {activePoint.day})
            </div>
            <div className="space-y-1">
              <div className="flex justify-between gap-4">
                <span className="text-slate-400">Index:</span>
                <span className="font-semibold text-blue-400">
                  {activePoint.index_value !== null ? activePoint.index_value.toFixed(1) : "Gap"}
                </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-slate-400">Avg Fare:</span>
                <span className="font-semibold text-white">
                  {formatINR(activePoint.fare)}
                </span>
              </div>
              {activePoint.change_pct !== undefined && activePoint.change_pct !== null && (
                <div className="flex justify-between gap-4 text-[10px] pt-1 border-t border-slate-800">
                  <span className="text-slate-400">Δ Day:</span>
                  <span className={activePoint.change_pct > 0 ? "text-blue-400" : "text-rose-400"}>
                    {formatPercent(activePoint.change_pct)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
