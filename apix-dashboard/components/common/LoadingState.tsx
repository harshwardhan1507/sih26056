import React from "react";

interface LoadingStateProps {
  label?: string;
  rows?: number;
  className?: string;
}

export function LoadingState({
  label = "Loading statistical observations...",
  rows = 4,
  className = "",
}: LoadingStateProps) {
  return (
    <div className={`py-8 animate-pulse ${className}`}>
      <div className="flex items-center gap-3 mb-6">
        <div className="h-2 w-2 rounded-full bg-[#176B5B] animate-ping" />
        <span className="font-mono text-xs text-[#626863] uppercase tracking-wider">
          {label}
        </span>
      </div>

      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="h-10 bg-[#D8D7D0]/30 rounded-xs w-full"
            style={{ opacity: 1 - i * 0.15 }}
          />
        ))}
      </div>
    </div>
  );
}
