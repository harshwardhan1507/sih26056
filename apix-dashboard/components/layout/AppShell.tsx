"use client";

import React from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { DataProvider, useData } from "@/lib/api/dataContext";

function ShellContent({ children }: { children: React.ReactNode }) {
  const { connectionStatus, toggleMode, lastCheckedIst } = useData();

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] flex flex-col font-sans">
      <Header
        connectionStatus={connectionStatus}
        onToggleMode={toggleMode}
        lastUpdated={lastCheckedIst}
      />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 px-8 py-8 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <DataProvider>
      <ShellContent>{children}</ShellContent>
    </DataProvider>
  );
}
