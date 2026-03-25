"use client";

import { useEffect } from "react";
import { useTallyStore } from "@/store/tally-store";
import { useClientStore } from "@/store/client-store";
import { Wifi, WifiOff } from "lucide-react";

/**
 * SIZH CA - Tally Connection Status Indicator
 * Shows green "Connected" or red "Disconnected" with active company name.
 */
export default function TallyStatusIndicator() {
  const { status, startPolling, stopPolling } = useTallyStore();
  const { activeClient } = useClientStore();

  useEffect(() => {
    startPolling(activeClient?.id || "global");
    return () => stopPolling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeClient?.id]);

  return (
    <div className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium">
      {status.connected ? (
        <>
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
          </span>
          <Wifi className="h-3.5 w-3.5 text-green-600" />
          <span className="text-green-700">Tally Connected</span>
          {status.companyName && (
            <span className="ml-1 max-w-[120px] truncate text-gray-500">
              — {status.companyName}
            </span>
          )}
        </>
      ) : (
        <>
          <span className="h-2 w-2 rounded-full bg-red-400" />
          <WifiOff className="h-3.5 w-3.5 text-red-500" />
          <span className="text-red-600">Tally Disconnected</span>
        </>
      )}
    </div>
  );
}
