import React from "react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title = "NO VALID OBSERVATIONS",
  description = "No valid matched observations were available for this selection.",
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`py-12 px-6 border border-dashed border-[#D8D7D0] bg-[#FAF9F5] rounded-sm text-center flex flex-col items-center justify-center ${className}`}
    >
      <div className="h-10 w-10 rounded-full bg-[#D8D7D0]/40 flex items-center justify-center text-[#626863] mb-3">
        <Inbox className="h-5 w-5" />
      </div>
      <h4 className="font-mono text-xs uppercase tracking-widest text-[#111716] font-semibold">
        {title}
      </h4>
      <p className="text-xs text-[#626863] mt-1 max-w-sm leading-relaxed">
        {description}
      </p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
