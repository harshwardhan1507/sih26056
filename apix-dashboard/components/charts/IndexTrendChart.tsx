"use client";

import React, { useState, useMemo, useRef } from "react";
import type { IndexPoint } from "@/lib/api/types";
import { formatPercent } from "@/lib/formatters/percentage";
import { Tabs } from "@/components/common/Tabs";

interface IndexTrendChartProps {
  data: IndexPoint[];
  baseValue?: number;
  timeframe: "7D" | "30D" | "90D";
  onTimeframeChange: (tf: "7D" | "30D" | "90D") => void;
  className?: string;
}

export function IndexTrendChart({
  data,
  baseValue = 100.0,
  timeframe,
  onTimeframeChange,
  className = "",
}: IndexTrendChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // Filter series based on timeframe
  const points = useMemo(() => {
    if (!data || data.length === 0) return [];
    const limit = timeframe === "7D" ? 7 : timeframe === "30D" ? 30 : 90;
    return data.slice(-limit);
  }, [data, timeframe]);

  // Valid values for scale calculation (excluding null gaps)
  const validValues = useMemo(() => {
    return points
      .map((p) => p.index_value)
      .filter((v): v is number => v !== null && v !== undefined && !Number.isNaN(v));
  }, [points]);

  // Dimensions & bounds
  const width = 800;
  const height = 280;
  const padLeft = 50;
  const padRight = 30;
  const padTop = 25;
  const padBottom = 35;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const { minVal, maxVal, yTicks } = useMemo(() => {
    if (validValues.length === 0) {
      return { minVal: 95, maxVal: 105, yTicks: [95, 100, 105] };
    }
    const rawMin = Math.min(...validValues, baseValue);
    const rawMax = Math.max(...validValues, baseValue);
    const padding = Math.max((rawMax - rawMin) * 0.15, 1.0);
    const min = Math.floor(rawMin - padding);
    const max = Math.ceil(rawMax + padding);

    // Generate 4-5 nice tick values
    const step = (max - min) / 4;
    const ticks: number[] = [];
    for (let i = 0; i <= 4; i++) {
      ticks.push(Number((min + i * step).toFixed(1)));
    }
    return { minVal: min, maxVal: max, yTicks: ticks };
  }, [validValues, baseValue]);

  // Scales
  const getX = (index: number) => {
    if (points.length <= 1) return padLeft + chartW / 2;
    return padLeft + (index / (points.length - 1)) * chartW;
  };

  const getY = (val: number) => {
    if (maxVal === minVal) return padTop + chartH / 2;
    return padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
  };

  // Build SVG path segments handling null gaps cleanly
  const pathSegments = useMemo(() => {
    if (points.length === 0) return [];
    const segments: string[] = [];
    let currentSegment: string[] = [];

    points.forEach((p, idx) => {
      if (p.index_value !== null && p.index_value !== undefined) {
        const x = getX(idx);
        const y = getY(p.index_value);
        if (currentSegment.length === 0) {
          currentSegment.push(`M ${x} ${y}`);
        } else {
          currentSegment.push(`L ${x} ${y}`);
        }
      } else {
        if (currentSegment.length > 0) {
          segments.push(currentSegment.join(" "));
          currentSegment = [];
        }
      }
    });

    if (currentSegment.length > 0) {
      segments.push(currentSegment.join(" "));
    }

    return segments;
  }, [points, minVal, maxVal]);

  // Area path for gradient fill
  const areaPath = useMemo(() => {
    if (points.length === 0) return "";
    const validPts: { x: number; y: number }[] = [];
    points.forEach((p, idx) => {
      if (p.index_value !== null && p.index_value !== undefined) {
        validPts.push({ x: getX(idx), y: getY(p.index_value) });
      }
    });
    if (validPts.length < 2) return "";

    const first = validPts[0];
    const last = validPts[validPts.length - 1];
    const bottomY = padTop + chartH;

    let path = `M ${first.x} ${bottomY} L ${first.x} ${first.y}`;
    for (let i = 1; i < validPts.length; i++) {
      path += ` L ${validPts[i].x} ${validPts[i].y}`;
    }
    path += ` L ${last.x} ${bottomY} Z`;
    return path;
  }, [points, minVal, maxVal]);

  // Hover interaction
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!containerRef.current || points.length === 0) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const relX = (mouseX / rect.width) * width;

    if (relX < padLeft || relX > width - padRight) {
      setHoverIndex(null);
      return;
    }

    const ratio = (relX - padLeft) / chartW;
    const closestIdx = Math.round(ratio * (points.length - 1));
    const clampedIdx = Math.max(0, Math.min(points.length - 1, closestIdx));
    setHoverIndex(clampedIdx);
  };

  const activePoint = hoverIndex !== null ? points[hoverIndex] : null;

  if (points.length === 0) {
    return (
      <div className="py-16 border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm text-center">
        <p className="font-mono text-xs text-[#626863] uppercase tracking-wider">
          No valid observations for this period
        </p>
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${className}`}>
      {/* Header with Timeframe Tabs */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="font-mono text-xs text-[#111716] uppercase tracking-wider font-semibold">
            India Airfare Index ({timeframe})
          </span>
          <span className="text-[11px] text-[#626863] ml-2 font-sans">
            Base ({baseValue.toFixed(1)}) = 100.0
          </span>
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

      {/* SVG Container */}
      <div
        ref={containerRef}
        className="relative w-full border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-3 select-none"
      >
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible cursor-crosshair"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            <linearGradient id="indexGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#176B5B" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#176B5B" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Horizontal Grid & Y-Axis Labels */}
          {yTicks.map((tick) => {
            const y = getY(tick);
            const isBase = Math.abs(tick - baseValue) < 0.05;
            return (
              <g key={tick}>
                <line
                  x1={padLeft}
                  y1={y}
                  x2={width - padRight}
                  y2={y}
                  stroke={isBase ? "#111716" : "#D8D7D0"}
                  strokeWidth={isBase ? 1 : 0.75}
                  strokeDasharray={isBase ? "4 3" : undefined}
                  opacity={isBase ? 0.7 : 0.6}
                />
                <text
                  x={padLeft - 8}
                  y={y + 3.5}
                  textAnchor="end"
                  className="text-[10px] font-mono fill-[#626863] tabular-nums"
                >
                  {tick.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* Base Level Indicator Tag */}
          <text
            x={width - padRight + 6}
            y={getY(baseValue) + 3}
            className="text-[9px] font-mono fill-[#626863] uppercase tracking-wider font-semibold"
          >
            Base
          </text>

          {/* Area gradient under line */}
          {areaPath && <path d={areaPath} fill="url(#indexGradient)" />}

          {/* Render Line Segments */}
          {pathSegments.map((d, i) => (
            <path
              key={i}
              d={d}
              fill="none"
              stroke="#176B5B"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}

          {/* Single-point plot marker if only 1 point exists */}
          {validValues.length === 1 && (
            <circle
              cx={getX(0)}
              cy={getY(validValues[0])}
              r="4"
              fill="#176B5B"
            />
          )}

          {/* X-Axis Date Ticks */}
          {points.length > 1 && (
            <>
              {/* Start Date */}
              <text
                x={padLeft}
                y={height - 8}
                textAnchor="start"
                className="text-[10px] font-mono fill-[#626863]"
              >
                {points[0].date}
              </text>
              {/* Mid Date */}
              <text
                x={padLeft + chartW / 2}
                y={height - 8}
                textAnchor="middle"
                className="text-[10px] font-mono fill-[#626863]"
              >
                {points[Math.floor(points.length / 2)].date}
              </text>
              {/* Latest Date */}
              <text
                x={width - padRight}
                y={height - 8}
                textAnchor="end"
                className="text-[10px] font-mono fill-[#626863]"
              >
                {points[points.length - 1].date}
              </text>
            </>
          )}

          {/* Hover Crosshair & Point */}
          {hoverIndex !== null && activePoint && (
            <g>
              {/* Vertical Crosshair Line */}
              <line
                x1={getX(hoverIndex)}
                y1={padTop}
                x2={getX(hoverIndex)}
                y2={padTop + chartH}
                stroke="#111716"
                strokeWidth="1"
                strokeDasharray="3 3"
                opacity="0.5"
              />

              {/* Highlight Point if valid */}
              {activePoint.index_value !== null && (
                <circle
                  cx={getX(hoverIndex)}
                  cy={getY(activePoint.index_value)}
                  r="5"
                  fill="#FAF9F5"
                  stroke="#176B5B"
                  strokeWidth="2.5"
                />
              )}
            </g>
          )}
        </svg>

        {/* Floating Tooltip Layer */}
        {hoverIndex !== null && activePoint && (
          <div
            className="absolute z-20 pointer-events-none p-2.5 bg-[#111716] text-[#FAF9F5] text-xs font-mono rounded-xs shadow-lg"
            style={{
              left: `${(getX(hoverIndex) / width) * 100}%`,
              top: "16px",
              transform: "translateX(-50%)",
            }}
          >
            <div className="text-[10px] text-[#A9C4B8] border-b border-stone-700 pb-1 mb-1">
              {activePoint.date} (Day {activePoint.day})
            </div>
            {activePoint.index_value !== null ? (
              <div className="space-y-0.5">
                <div className="flex justify-between gap-3">
                  <span className="text-[#A9C4B8]">Index:</span>
                  <span className="font-semibold text-white">
                    {activePoint.index_value.toFixed(1)}
                  </span>
                </div>
                {activePoint.change_pct !== undefined && activePoint.change_pct !== null && (
                  <div className="flex justify-between gap-3 text-[11px]">
                    <span className="text-[#A9C4B8]">Δ Day:</span>
                    <span
                      className={
                        activePoint.change_pct > 0
                          ? "text-emerald-400"
                          : activePoint.change_pct < 0
                          ? "text-rose-400"
                          : "text-stone-300"
                      }
                    >
                      {formatPercent(activePoint.change_pct)}
                    </span>
                  </div>
                )}
                {activePoint.quotes !== undefined && (
                  <div className="flex justify-between gap-3 text-[10px] text-stone-400 pt-0.5 border-t border-stone-800">
                    <span>Quotes:</span>
                    <span>{activePoint.quotes}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-amber-300 text-[11px] italic">
                Gap: No valid observations
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
