import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  onSwitchToDemo?: () => void;
  className?: string;
}

export function ErrorState({
  title = "API SERVICE UNAVAILABLE",
  message = "The live FastAPI service at localhost:8000 is unreachable.",
  onRetry,
  onSwitchToDemo,
  className = "",
}: ErrorStateProps) {
  return (
    <div
      className={`py-12 px-6 border border-rose-200 bg-rose-50/60 rounded-sm text-center flex flex-col items-center justify-center ${className}`}
    >
      <div className="h-10 w-10 rounded-full bg-rose-100 flex items-center justify-center text-rose-600 mb-3">
        <AlertCircle className="h-5 w-5" />
      </div>
      <h4 className="font-mono text-xs uppercase tracking-widest text-rose-700 font-bold">
        {title}
      </h4>
      <p className="text-xs text-[#64748B] mt-1 max-w-md leading-relaxed">
        {message}
      </p>

      <div className="mt-5 flex items-center gap-3">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E8F0] rounded-xs text-xs font-mono text-[#0F172A] hover:bg-slate-50 cursor-pointer transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Retry Connection</span>
          </button>
        )}

        {onSwitchToDemo && (
          <button
            type="button"
            onClick={onSwitchToDemo}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#1E3A8A] text-white rounded-xs text-xs font-mono hover:bg-[#1E3A8A]/90 cursor-pointer transition-colors shadow-xs"
          >
            <span>Switch to Local Demo</span>
          </button>
        )}
      </div>
    </div>
  );
}
