"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { ApiXDataProvider } from "./provider";
import { fixtureProvider } from "./fixtureProvider";
import { fastApiProvider } from "./fastApiProvider";
import type { ConnectionStatus } from "./types";
import { getCurrentISTHeaderDate } from "../formatters/dates";
import { config } from "../config";

interface DataContextType {
  provider: ApiXDataProvider;
  connectionStatus: ConnectionStatus;
  isDemoMode: boolean;
  lastCheckedIst: string;
  switchToLive: () => Promise<void>;
  switchToDemo: () => void;
  toggleMode: () => Promise<void>;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export function DataProvider({ children }: { children: ReactNode }) {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("LOCAL_DEMO");
  const [provider, setProvider] = useState<ApiXDataProvider>(fixtureProvider);
  const [lastCheckedIst, setLastCheckedIst] = useState<string>(getCurrentISTHeaderDate());

  const switchToDemo = useCallback(() => {
    setProvider(fixtureProvider);
    setConnectionStatus("LOCAL_DEMO");
    setLastCheckedIst(getCurrentISTHeaderDate());
  }, []);

  const switchToLive = useCallback(async () => {
    if (!config.isLiveApiConfigured()) {
      // If no API URL configured, immediately flag as API_UNAVAILABLE (no silent fake live)
      setConnectionStatus("API_UNAVAILABLE");
      return;
    }

    try {
      const baseUrl = config.getEffectiveApiBaseUrl();
      const res = await fetch(`${baseUrl}/health`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        // Live server responded
        setProvider(fastApiProvider);
        setConnectionStatus("LIVE_CONNECTED");
        setLastCheckedIst(getCurrentISTHeaderDate());
      } else {
        setConnectionStatus("API_UNAVAILABLE");
      }
    } catch {
      // Live server down or unreachable - explicit unavailable state, NO silent fallback
      setConnectionStatus("API_UNAVAILABLE");
    }
  }, []);

  const toggleMode = useCallback(async () => {
    if (connectionStatus === "LOCAL_DEMO") {
      await switchToLive();
    } else {
      switchToDemo();
    }
  }, [connectionStatus, switchToLive, switchToDemo]);

  // Periodic heartbeat if live
  useEffect(() => {
    if (connectionStatus !== "LIVE_CONNECTED") return;

    const interval = setInterval(async () => {
      try {
        const baseUrl = config.getEffectiveApiBaseUrl();
        const res = await fetch(`${baseUrl}/health`, { signal: AbortSignal.timeout(4000) });
        if (!res.ok) {
          setConnectionStatus("API_UNAVAILABLE");
        } else {
          setLastCheckedIst(getCurrentISTHeaderDate());
        }
      } catch {
        setConnectionStatus("API_UNAVAILABLE");
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [connectionStatus]);

  const value: DataContextType = {
    provider,
    connectionStatus,
    isDemoMode: connectionStatus === "LOCAL_DEMO",
    lastCheckedIst,
    switchToLive,
    switchToDemo,
    toggleMode,
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useData(): DataContextType {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error("useData must be used within a DataProvider");
  }
  return context;
}
