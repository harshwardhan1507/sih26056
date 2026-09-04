import React from "react";

interface SparklineProps {
  data: (number | null)[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}

export function Sparkline({
  data,
  width = 60,
  height = 20,
  color = "#1E3A8A",
  className = "",
}: SparklineProps) {
  const valid = data.filter((v): v is number => v !== null && v !== undefined && !Number.isNaN(v));

  if (valid.length < 2) {
    return (
      <span className="text-[10px] font-mono text-[#64748B]/50 italic">—</span>
    );
  }

  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const range = max - min || 1;

  const pad = 2;
  const w = width - pad * 2;
  const h = height - pad * 2;

  const points = data.map((val, idx) => {
    if (val === null || val === undefined) return null;
    const x = pad + (idx / (data.length - 1)) * w;
    const y = pad + h - ((val - min) / range) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  // Build segments handling nulls
  const segments: string[] = [];
  let current: string[] = [];

  points.forEach((pt) => {
    if (pt !== null) {
      current.push(pt);
    } else {
      if (current.length > 1) {
        segments.push(`M ${current.join(" L ")}`);
      }
      current = [];
    }
  });

  if (current.length > 1) {
    segments.push(`M ${current.join(" L ")}`);
  }

  return (
    <svg
      width={width}
      height={height}
      className={`overflow-visible inline-block ${className}`}
    >
      {segments.map((d, i) => (
        <path
          key={i}
          d={d}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
    </svg>
  );
}
