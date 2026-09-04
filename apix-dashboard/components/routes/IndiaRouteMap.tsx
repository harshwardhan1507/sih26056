"use client";

import React, { useState, useMemo } from "react";
import type { RouteSnapshot } from "@/lib/api/types";
import {
  INDIA_COUNTRY_PATH,
  INDIA_STATES_PATH,
  AIRPORT_HUBS,
  MapHub,
} from "./indiaMapData";
import { Plane, BarChart3 } from "lucide-react";

interface IndiaRouteMapProps {
  routes: RouteSnapshot[];
  selectedRouteId?: string | null;
  onSelectRoute?: (routeId: string) => void;
  className?: string;
}

export function IndiaRouteMap({
  routes,
  selectedRouteId,
  onSelectRoute,
  className = "",
}: IndiaRouteMapProps) {
  const [hoveredRouteId, setHoveredRouteId] = useState<string | null>(null);
  const [hoveredHub, setHoveredHub] = useState<string | null>(null);

  // Sort routes by passenger traffic weight descending
  const sortedRoutes = useMemo(() => {
    return [...routes].sort((a, b) => b.weight - a.weight);
  }, [routes]);

  // Determine top route by weight
  const topRoute = useMemo(() => {
    return sortedRoutes.length > 0 ? sortedRoutes[0] : null;
  }, [sortedRoutes]);

  // Active route is either hovered or selected
  const activeRouteId = hoveredRouteId || selectedRouteId;
  const activeRoute = useMemo(() => {
    if (!activeRouteId) return null;
    return routes.find((r) => r.route_id === activeRouteId) || null;
  }, [activeRouteId, routes]);

  // Unique hubs present in the active route basket
  const activeHubs = useMemo(() => {
    const hubCodes = new Set<string>();
    routes.forEach((r) => {
      hubCodes.add(r.origin);
      hubCodes.add(r.destination);
    });

    // Also include other major cities present in the map data for visual completeness
    const result: MapHub[] = [];
    Object.values(AIRPORT_HUBS).forEach((hub) => {
      if (hubCodes.has(hub.code)) {
        result.push(hub);
      }
    });
    return result;
  }, [routes]);

  // Precompute curved flight paths for all routes
  const mapEdges = useMemo(() => {
    const center = { x: 210, y: 380 };

    return routes
      .map((r) => {
        const from = AIRPORT_HUBS[r.origin];
        const to = AIRPORT_HUBS[r.destination];
        if (!from || !to) return null;

        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const dist = Math.hypot(dx, dy);
        let px = -dy / dist;
        let py = dx / dist;

        // Curve outward away from central India
        const mx = (from.x + to.x) / 2;
        const my = (from.y + to.y) / 2;
        const vx = mx - center.x;
        const vy = my - center.y;

        if (px * vx + py * vy < 0) {
          px = -px;
          py = -py;
        }

        const curvature = 0.15;
        const cx = Math.round((mx + px * dist * curvature) * 10) / 10;
        const cy = Math.round((my + py * dist * curvature) * 10) / 10;
        const pathD = `M ${from.x},${from.y} Q ${cx},${cy} ${to.x},${to.y}`;

        // Dynamic stroke width mapped to DGCA passenger traffic share
        // Top routes (e.g. 19%) ~ 4.5px, lower routes (e.g. 4%) ~ 1.5px
        const strokeWidth = Math.max(1.5, Math.min(5.5, r.weight * 24));

        return {
          route: r,
          from,
          to,
          cx,
          cy,
          pathD,
          strokeWidth,
        };
      })
      .filter((e): e is NonNullable<typeof e> => e !== null);
  }, [routes]);

  return (
    <div
      className={`border border-[#D8DCE3] bg-white rounded-xl p-5 md:p-6 shadow-xs ${className}`}
    >
      {/* Component Title & Subtitle */}
      <div className="pb-4 mb-4 border-b border-[#E2E8F0] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h3 className="font-sans text-lg md:text-xl font-bold tracking-tight text-[#1E3A8A]">
            ROUTE NETWORK (INDIA)
          </h3>
          <p className="text-xs md:text-sm text-[#64748B] mt-0.5">
            12 major domestic routes, weighted by actual passenger traffic (DGCA)
          </p>
        </div>

        {activeRoute && (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#EFF6FF] border border-[#BFDBFE] text-xs font-mono text-[#1E40AF]">
            <span className="font-bold">{activeRoute.origin} ↔ {activeRoute.destination}</span>
            <span className="font-semibold text-[#2563EB]">
              {(activeRoute.weight * 100).toFixed(1)}% weight
            </span>
          </div>
        )}
      </div>

      {/* Main Grid: Map on Left + Sidebar on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Authentic India SVG Map with Flight Network */}
        <div className="lg:col-span-8 flex flex-col justify-between">
          <div className="relative w-full aspect-[580/620] max-h-[580px] flex items-center justify-center select-none bg-white rounded-lg">
            <svg
              viewBox="0 0 580 620"
              className="w-full h-full max-h-[580px] overflow-visible"
              aria-label="India Domestic Flight Route Network Map"
            >
              <defs>
                {/* Subtle drop shadow filter for highlighted flight paths */}
                <filter id="route-glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="0" dy="1" stdDeviation="3" floodColor="#2563EB" floodOpacity="0.4" />
                </filter>
                {/* Gradient for highest traffic paths */}
                <linearGradient id="trunk-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#1E40AF" />
                  <stop offset="100%" stopColor="#3B82F6" />
                </linearGradient>
              </defs>

              {/* 1. Base Fill: Official Survey of India Country Boundary */}
              <path
                d={INDIA_COUNTRY_PATH}
                fill="#F4F8FD"
                stroke="#BFDBFE"
                strokeWidth="1.25"
                strokeLinejoin="round"
                className="transition-colors"
              />

              {/* 2. Internal State Boundaries (subtle dashed lines) */}
              <path
                d={INDIA_STATES_PATH}
                fill="none"
                stroke="#CBD5E1"
                strokeWidth="0.65"
                strokeDasharray="2,2"
                opacity="0.6"
              />

              {/* 3. Flight Network Bezier Curves */}
              <g className="routes-layer">
                {mapEdges.map(({ route, pathD, strokeWidth }) => {
                  const isHovered = hoveredRouteId === route.route_id;
                  const isSelected = selectedRouteId === route.route_id;
                  const isHubConnected =
                    hoveredHub !== null &&
                    (route.origin === hoveredHub || route.destination === hoveredHub);
                  const isHighlighted = isHovered || isSelected || isHubConnected;
                  const isDimmed = activeRouteId !== null && !isHighlighted;

                  return (
                    <g
                      key={route.route_id}
                      className="cursor-pointer group"
                      onMouseEnter={() => setHoveredRouteId(route.route_id)}
                      onMouseLeave={() => setHoveredRouteId(null)}
                      onClick={() => onSelectRoute && onSelectRoute(route.route_id)}
                    >
                      {/* Generous invisible hit area for easy hover/click */}
                      <path
                        d={pathD}
                        fill="none"
                        stroke="transparent"
                        strokeWidth="18"
                      />

                      {/* Visible flight route arc */}
                      <path
                        d={pathD}
                        fill="none"
                        stroke={isHighlighted ? "#1D4ED8" : "#2563EB"}
                        strokeWidth={isHighlighted ? strokeWidth + 2 : strokeWidth}
                        strokeOpacity={
                          isDimmed
                            ? 0.18
                            : isHighlighted
                            ? 1.0
                            : Math.max(0.4, Math.min(0.85, route.weight * 3.8))
                        }
                        strokeLinecap="round"
                        filter={isHighlighted ? "url(#route-glow)" : undefined}
                        className="transition-all duration-200"
                      />
                    </g>
                  );
                })}
              </g>

              {/* 4. Major Airport Hub Nodes & Labels */}
              <g className="nodes-layer">
                {activeHubs.map((hub) => {
                  const isHovered = hoveredHub === hub.code;
                  const isConnectedToActiveRoute =
                    activeRoute !== null &&
                    (activeRoute.origin === hub.code || activeRoute.destination === hub.code);

                  const isNodeHighlighted = isHovered || isConnectedToActiveRoute;

                  // Label anchor and positioning calculations
                  let anchor: "start" | "end" | "middle" = "middle";
                  let codeX = hub.x;
                  let codeY = hub.y - 12;
                  let nameX = hub.x;
                  let nameY = hub.y - 2;

                  if (hub.labelPos === "left") {
                    anchor = "end";
                    codeX = hub.x - 10;
                    codeY = hub.y - 1;
                    nameX = hub.x - 10;
                    nameY = hub.y + 10;
                  } else if (hub.labelPos === "right") {
                    anchor = "start";
                    codeX = hub.x + 10;
                    codeY = hub.y - 1;
                    nameX = hub.x + 10;
                    nameY = hub.y + 10;
                  } else if (hub.labelPos === "bottom") {
                    anchor = "middle";
                    codeX = hub.x;
                    codeY = hub.y + 16;
                    nameX = hub.x;
                    nameY = hub.y + 27;
                  }

                  return (
                    <g
                      key={hub.code}
                      className="cursor-pointer group select-none"
                      onMouseEnter={() => setHoveredHub(hub.code)}
                      onMouseLeave={() => setHoveredHub(null)}
                    >
                      {/* Outer ripple ring on highlight */}
                      {isNodeHighlighted && (
                        <circle
                          cx={hub.x}
                          cy={hub.y}
                          r="12"
                          fill="#DBEAFE"
                          opacity="0.6"
                          className="animate-pulse"
                        />
                      )}

                      {/* Airport Node Circle */}
                      <circle
                        cx={hub.x}
                        cy={hub.y}
                        r={isNodeHighlighted ? 6.5 : 5}
                        fill="#1E40AF"
                        stroke="#FFFFFF"
                        strokeWidth="2"
                        className="transition-all duration-150"
                      />

                      {/* Airport IATA Code */}
                      <text
                        x={codeX}
                        y={codeY}
                        textAnchor={anchor}
                        className={`text-[11px] font-mono tracking-tight ${
                          isNodeHighlighted
                            ? "fill-[#1E3A8A] font-bold text-xs"
                            : "fill-[#0F172A] font-bold"
                        }`}
                      >
                        {hub.code}
                      </text>

                      {/* City Name */}
                      <text
                        x={nameX}
                        y={nameY}
                        textAnchor={anchor}
                        className={`text-[9.5px] font-sans ${
                          isNodeHighlighted
                            ? "fill-[#1E40AF] font-semibold"
                            : "fill-[#475569] font-medium"
                        }`}
                      >
                        {hub.name}
                      </text>
                    </g>
                  );
                })}
              </g>
            </svg>
          </div>

          {/* Bottom Map Legend */}
          <div className="pt-4 mt-2 border-t border-[#E2E8F0] flex flex-wrap items-center justify-between gap-4 text-xs font-sans text-[#475569]">
            <div className="flex flex-wrap items-center gap-5 sm:gap-6">
              {/* Higher traffic legend item */}
              <div className="flex items-center gap-2">
                <span className="h-1.5 w-7 rounded-full bg-[#2563EB]" />
                <span className="font-medium text-[#0F172A]">Higher traffic (thicker line)</span>
              </div>

              {/* Lower traffic legend item */}
              <div className="flex items-center gap-2">
                <span className="h-0.5 w-7 rounded-full bg-[#93C5FD]" />
                <span className="font-medium text-[#64748B]">Lower traffic (thinner line)</span>
              </div>

              {/* Major airport legend item */}
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-[#1E40AF] border-2 border-white ring-1 ring-[#1E40AF]" />
                <span className="font-medium text-[#0F172A]">Major airport ({activeHubs.length} hubs)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Top Route + Route List + DGCA Callout */}
        <div className="lg:col-span-4 space-y-4">
          {/* Card 1: Top Route Hero Box */}
          {topRoute && (
            <div
              onClick={() => onSelectRoute && onSelectRoute(topRoute.route_id)}
              className="bg-[#F0F6FF] border border-[#DBEAFE] rounded-xl p-4 transition-all hover:border-[#93C5FD] cursor-pointer shadow-2xs"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-[#64748B]">
                    Top Route
                  </span>
                  <div className="text-xl font-bold text-[#1E3A8A]">
                    {topRoute.origin} ↔ {topRoute.destination}
                  </div>
                  <div className="text-2xl font-extrabold text-[#2563EB] font-mono tracking-tight">
                    {(topRoute.weight * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-[#64748B]">
                    of total domestic traffic
                  </div>
                </div>

                <div className="p-2.5 bg-[#2563EB] text-white rounded-xl shadow-xs">
                  <Plane className="h-5 w-5" />
                </div>
              </div>
            </div>
          )}

          {/* Card 2: ROUTE LIST (12) */}
          <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-4 shadow-2xs">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#E2E8F0]">
              <h4 className="font-mono text-xs uppercase tracking-wider text-[#0F172A] font-bold">
                ROUTE LIST ({sortedRoutes.length})
              </h4>
              <span className="text-[10px] font-mono text-[#64748B]">
                DGCA T12M Share
              </span>
            </div>

            <div className="space-y-1 max-h-[300px] overflow-y-auto pr-1">
              {sortedRoutes.map((r, idx) => {
                const isSelected = selectedRouteId === r.route_id;
                const isHovered = hoveredRouteId === r.route_id;

                return (
                  <div
                    key={r.route_id}
                    onMouseEnter={() => setHoveredRouteId(r.route_id)}
                    onMouseLeave={() => setHoveredRouteId(null)}
                    onClick={() => onSelectRoute && onSelectRoute(r.route_id)}
                    className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-colors cursor-pointer ${
                      isSelected
                        ? "bg-[#2563EB] text-white font-bold shadow-2xs"
                        : isHovered
                        ? "bg-[#EFF6FF] text-[#1E3A8A] font-semibold"
                        : "text-[#334155] hover:bg-slate-100/80"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[11px] w-4 ${
                          isSelected ? "text-blue-100" : "text-[#94A3B8]"
                        }`}
                      >
                        {idx + 1}.
                      </span>
                      <span>
                        {r.origin} ↔ {r.destination}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[11px] font-semibold tabular-nums ${
                          isSelected ? "text-white" : "text-[#1E40AF]"
                        }`}
                      >
                        {(r.weight * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Card 3: DGCA Passenger Weighting Note */}
          <div className="bg-[#EFF6FF] border border-[#BFDBFE] rounded-xl p-3.5 flex items-start gap-3 text-xs shadow-2xs">
            <div className="p-1.5 bg-[#DBEAFE] text-[#1E40AF] rounded-lg mt-0.5 shrink-0">
              <BarChart3 className="h-4 w-4 text-[#2563EB]" />
            </div>
            <p className="text-[#1E40AF] font-medium leading-snug">
              Routes are weighted using actual passenger traffic as per DGCA data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
