"use client";

import React, { useState, useMemo } from "react";
import type { RouteSnapshot } from "@/lib/api/types";

interface IndiaRouteMapProps {
  routes: RouteSnapshot[];
  selectedRouteId?: string | null;
  onSelectRoute?: (routeId: string) => void;
  className?: string;
}

interface HubNode {
  code: string;
  name: string;
  x: number;
  y: number;
}

// Geometric coordinates approximating India's domestic hub network layout
const HUBS: Record<string, HubNode> = {
  DEL: { code: "DEL", name: "Delhi", x: 260, y: 110 },
  BOM: { code: "BOM", name: "Mumbai", x: 140, y: 280 },
  BLR: { code: "BLR", name: "Bengaluru", x: 220, y: 440 },
  CCU: { code: "CCU", name: "Kolkata", x: 440, y: 230 },
  MAA: { code: "MAA", name: "Chennai", x: 290, y: 450 },
  HYD: { code: "HYD", name: "Hyderabad", x: 245, y: 320 },
  GOI: { code: "GOI", name: "Goa", x: 155, y: 375 },
};

export function IndiaRouteMap({
  routes,
  selectedRouteId,
  onSelectRoute,
  className = "",
}: IndiaRouteMapProps) {
  const [hoveredRouteId, setHoveredRouteId] = useState<string | null>(null);
  const [hoveredHub, setHoveredHub] = useState<string | null>(null);

  // Map route objects to coordinate pairs
  const mapEdges = useMemo(() => {
    return routes
      .map((r) => {
        const from = HUBS[r.origin];
        const to = HUBS[r.destination];
        if (!from || !to) return null;

        // Stroke thickness mapped to DGCA weight (range ~1.5px to 5px)
        const strokeWidth = Math.max(1.5, Math.min(5.5, r.weight * 22));

        return {
          route: r,
          from,
          to,
          strokeWidth,
        };
      })
      .filter((e): e is NonNullable<typeof e> => e !== null);
  }, [routes]);

  const activeRoute = useMemo(() => {
    const targetId = hoveredRouteId || selectedRouteId;
    if (!targetId) return null;
    return routes.find((r) => r.route_id === targetId) || null;
  }, [hoveredRouteId, selectedRouteId, routes]);

  return (
    <div
      className={`border border-[#E2E8F0] bg-white rounded-sm p-4 relative shadow-xs ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-[#E2E8F0]">
        <div>
          <h4 className="font-mono text-xs uppercase tracking-widest text-[#0F172A] font-semibold">
            Route Network Graphic
          </h4>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            12 major domestic routes, weighted by actual passenger traffic (DGCA)
          </p>
        </div>

        {activeRoute && (
          <div className="text-right font-mono text-xs">
            <span className="font-bold text-[#0F172A]">{activeRoute.origin} ↔ {activeRoute.destination}</span>
            <span className="text-[#1E3A8A] ml-2 font-semibold">
              {(activeRoute.weight * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      <div className="relative w-full aspect-[4/3] max-h-[440px] flex items-center justify-center select-none bg-white">
        <svg
          viewBox="0 0 520 500"
          className="w-full h-full max-h-[440px] overflow-visible"
        >
          {/* Subtle network compass/radar background */}
          <g opacity="0.05" fill="#1E3A8A">
            <circle cx="260" cy="270" r="180" />
          </g>

          {/* Route Connection Lines */}
          {mapEdges.map(({ route, from, to, strokeWidth }) => {
            const isHovered = hoveredRouteId === route.route_id;
            const isSelected = selectedRouteId === route.route_id;
            const isHubConnected =
              hoveredHub !== null &&
              (route.origin === hoveredHub || route.destination === hoveredHub);

            const isHighlighted = isHovered || isSelected || isHubConnected;

            return (
              <g
                key={route.route_id}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredRouteId(route.route_id)}
                onMouseLeave={() => setHoveredRouteId(null)}
                onClick={() => onSelectRoute && onSelectRoute(route.route_id)}
              >
                {/* Wider invisible hit area */}
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="transparent"
                  strokeWidth="16"
                />

                {/* Visible route stroke */}
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke={isHighlighted ? "#2563EB" : "#1E3A8A"}
                  strokeWidth={isHighlighted ? strokeWidth + 1.5 : strokeWidth}
                  strokeOpacity={isHighlighted ? 0.95 : 0.45}
                  strokeLinecap="round"
                  className="transition-all duration-150"
                />
              </g>
            );
          })}

          {/* Hub City Nodes */}
          {Object.values(HUBS).map((hub) => {
            const isHovered = hoveredHub === hub.code;

            return (
              <g
                key={hub.code}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredHub(hub.code)}
                onMouseLeave={() => setHoveredHub(null)}
              >
                {/* Outer ring */}
                <circle
                  cx={hub.x}
                  cy={hub.y}
                  r={isHovered ? 7 : 5}
                  fill="#FFFFFF"
                  stroke={isHovered ? "#2563EB" : "#1E3A8A"}
                  strokeWidth="2"
                  className="transition-all"
                />
                {/* Center dot */}
                <circle
                  cx={hub.x}
                  cy={hub.y}
                  r="2"
                  fill={isHovered ? "#2563EB" : "#1E3A8A"}
                />

                {/* Label */}
                <text
                  x={hub.x + 8}
                  y={hub.y + 4}
                  className={`text-[11px] font-mono select-none ${
                    isHovered
                      ? "fill-[#1E3A8A] font-bold"
                      : "fill-[#0F172A] font-semibold"
                  }`}
                >
                  {hub.code}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Map Legend */}
      <div className="pt-2 border-t border-[#E2E8F0] flex items-center justify-between text-[10px] font-mono text-[#64748B]">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="h-1 w-5 rounded-full bg-[#1E3A8A] opacity-80" />
            <span>Route (both directions)</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-5 rounded-full bg-[#1E3A8A] opacity-40" />
            <span>Line thickness = DGCA weight</span>
          </span>
        </div>
      </div>
    </div>
  );
}
