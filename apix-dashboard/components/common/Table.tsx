import React from "react";

interface TableProps {
  headers: React.ReactNode[];
  children: React.ReactNode;
  className?: string;
}

export function Table({ headers, children, className = "" }: TableProps) {
  return (
    <div className={`overflow-x-auto w-full ${className}`}>
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="border-b border-[#E2E8F0] bg-slate-50/70">
            {headers.map((header, idx) => (
              <th
                key={idx}
                className="py-2.5 px-3 font-mono uppercase tracking-wider text-[10px] text-[#64748B] font-semibold"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#E2E8F0] font-sans">
          {children}
        </tbody>
      </table>
    </div>
  );
}
