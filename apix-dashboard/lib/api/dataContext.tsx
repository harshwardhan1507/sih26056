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

  /**
   * Enter the API_UNAVAILABLE state.
   *
   * The provider is reset to the fixture provider on the way in. Previously
   * only the status changed: `provider` was left as whatever it was, so a
   * failed connection attempt left the pages rendering FIXTURE data under a red
   * "API Unavailable" badge with `isDemoMode === false` — no indication at all
   * that the numbers on screen were demo data. And because page effects depend
   * on `provider`, an unchanged provider did not even re-render.
   */
  const markUnavailable = useCallback(() => {
    setProvider(fixtureProvider);
    setConnectionStatus("API_UNAVAILABLE");
    setLastCheckedIst(getCurrentISTHeaderDate());
  }, []);

  const switchToLive = useCallback(async () => {
    if (!config.isLiveApiConfigured()) {
      markUnavailable();
      return;
    }

    try {
      const baseUrl = config.getEffectiveApiBaseUrl();
      const res = await fetch(`${baseUrl}/health`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        setProvider(fastApiProvider);
        setConnectionStatus("LIVE_CONNECTED");
        setLastCheckedIst(getCurrentISTHeaderDate());
      } else {
        markUnavailable();
      }
    } catch {
      // Live server down or unreachable — explicit unavailable state, and the
      // provider falls back so what is displayed matches what is claimed.
      markUnavailable();
    }
  }, [markUnavailable]);

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
          markUnavailable();
        } else {
          setLastCheckedIst(getCurrentISTHeaderDate());
        }
      } catch {
        // A live server that dies mid-session must also drop the provider:
        // leaving fastApiProvider in place made every later call throw.
        markUnavailable();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [connectionStatus, markUnavailable]);

  const value: DataContextType = {
    provider,
    connectionStatus,
    // True whenever the displayed numbers come from fixtures — which includes
    // API_UNAVAILABLE, since that state now falls back to the fixture provider.
    isDemoMode: connectionStatus !== "LIVE_CONNECTED",
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
