"use client";

import React from "react";
import type { AdvanceWindow, WindowDetail } from "@/lib/api/types";
import { formatINR } from "@/lib/formatters/currency";

interface HorizonDecayChartProps {
  windows: Record<AdvanceWindow, WindowDetail>;
  activeWindow: AdvanceWindow;
  onSelectWindow: (w: AdvanceWindow) => void;
  className?: string;
}

const HORIZONS: AdvanceWindow[] = ["T+1", "T+7", "T+15", "T+30", "T+45"];

export function HorizonDecayChart({
  windows,
  activeWindow,
  onSelectWindow,
  className = "",
}: HorizonDecayChartProps) {
  // Extract fares
  const validFares = HORIZONS.map((h) => windows[h]?.average_fare).filter(
    (f): f is number => f !== null && f !== undefined && !Number.isNaN(f)
  );

  const maxFare = validFares.length > 0 ? Math.max(...validFares) * 1.15 : 10000;

  const width = 600;
  const height = 180;
  const padLeft = 40;
  const padRight = 30;
  const padTop = 25;
  const padBottom = 35;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;
  const barWidth = Math.min(60, chartW / (HORIZONS.length * 1.5));

  return (
    <div
      className={`border border-[#D8D7D0] bg-[#FAF9F5] rounded-sm p-4 ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-[#D8D7D0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#111716] font-semibold">
            Advance-Purchase Price Decay
          </h4>
          <p className="text-[11px] text-[#626863] mt-0.5">
            Average consumer fare progression by lead purchase horizon
          </p>
        </div>
        <span className="text-[10px] font-mono text-[#626863]">
          Active: <strong className="text-[#176B5B]">{activeWindow}</strong>
        </span>
      </div>

      <div className="relative w-full aspect-[16/6] max-h-[220px]">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
          {/* Recessive Grid Lines */}
          {[0, 0.33, 0.66, 1].map((ratio) => {
            const y = padTop + chartH * (1 - ratio);
            const val = Math.round(maxFare * ratio);
            return (
              <g key={ratio}>
                <line
                  x1={padLeft}
                  y1={y}
                  x2={width - padRight}
                  y2={y}
                  stroke="#D8D7D0"
                  strokeWidth="0.6"
                  opacity="0.6"
                />
                <text
                  x={padLeft - 6}
                  y={y + 3}
                  textAnchor="end"
                  className="text-[9px] font-mono fill-[#626863] tabular-nums"
                >
                  ₹{(val / 1000).toFixed(0)}k
                </text>
              </g>
            );
          })}

          {/* Horizon Bars */}
          {HORIZONS.map((h, idx) => {
            const win = windows[h];
            const fare = win?.average_fare;
            const isAvailable = win?.available && fare !== null && fare !== undefined;
            const isActive = activeWindow === h;

            const xCenter = padLeft + (idx / (HORIZONS.length - 1)) * chartW;
            const barH = isAvailable ? (fare! / maxFare) * chartH : 10;
            const yTop = padTop + chartH - barH;

            return (
              <g
                key={h}
                onClick={() => isAvailable && onSelectWindow(h)}
                className={isAvailable ? "cursor-pointer group" : "cursor-not-allowed opacity-40"}
              >
                {/* Bar */}
                <rect
                  x={xCenter - barWidth / 2}
                  y={yTop}
                  width={barWidth}
                  height={barH}
                  rx="2"
                  fill={
                    !isAvailable
                      ? "#D8D7D0"
                      : isActive
                      ? "#176B5B"
                      : "#626863"
                  }
                  fillOpacity={isActive ? 0.95 : 0.4}
                  className="transition-all duration-150 group-hover:fill-opacity-80"
                />

                {/* Direct Value Label on Top */}
                {isAvailable ? (
                  <text
                    x={xCenter}
                    y={yTop - 6}
                    textAnchor="middle"
                    className={`text-[10px] font-mono font-bold tabular-nums ${
                      isActive ? "fill-[#176B5B]" : "fill-[#111716]"
                    }`}
                  >
                    {formatINR(fare)}
                  </text>
                ) : (
                  <text
                    x={xCenter}
                    y={yTop - 6}
                    textAnchor="middle"
                    className="text-[9px] font-mono fill-[#626863] italic"
                  >
                    N/A
                  </text>
                )}

                {/* Horizon X Label */}
                <text
                  x={xCenter}
                  y={height - 12}
                  textAnchor="middle"
                  className={`text-[11px] font-mono font-semibold ${
                    isActive ? "fill-[#176B5B] underline" : "fill-[#111716]"
                  }`}
                >
                  {h}
                </text>

                <text
                  x={xCenter}
                  y={height - 2}
                  textAnchor="middle"
                  className="text-[8px] font-sans fill-[#626863]"
                >
                  {h === "T+1"
                    ? "1 day lead"
                    : h === "T+7"
                    ? "1 week"
                    : h === "T+15"
                    ? "2 weeks"
                    : h === "T+30"
                    ? "1 month"
                    : "45 days"}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
