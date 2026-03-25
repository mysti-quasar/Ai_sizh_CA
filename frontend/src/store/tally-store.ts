import { create } from "zustand";
import api from "@/lib/api";

/**
 * SIZH CA - Tally Connection Store
 * Tracks real-time Tally ERP/Prime connection status.
 */

const TALLY_CONNECTOR_URL =
  process.env.NEXT_PUBLIC_TALLY_CONNECTOR_URL || "http://127.0.0.1:8765";

interface TallyStatus {
  connected: boolean;
  companyName: string | null;
  tallyVersion: string | null;
  connectedAt: string | null;
}

interface TallyState {
  status: TallyStatus;
  isPolling: boolean;
  fetchStatus: (clientId: string) => Promise<void>;
  startPolling: (clientId: string) => void;
  stopPolling: () => void;
  syncLedgers: (clientId: string) => Promise<void>;
  syncItems: (clientId: string) => Promise<void>;
}

let pollInterval: ReturnType<typeof setInterval> | null = null;

export const useTallyStore = create<TallyState>()((set, get) => ({
  status: {
    connected: false,
    companyName: null,
    tallyVersion: null,
    connectedAt: null,
  },
  isPolling: false,

  fetchStatus: async (clientId: string) => {
    void clientId;
    try {
      const res = await fetch(`${TALLY_CONNECTOR_URL}/tally/status`);
      if (!res.ok) {
        throw new Error(`Status request failed: ${res.status}`);
      }
      const data = await res.json();

      const connected =
        typeof data.connected === "boolean"
          ? data.connected
          : Boolean(data.running);
      const companyName =
        (typeof data.company_name === "string" && data.company_name) ||
        (typeof data.companyName === "string" && data.companyName) ||
        null;

      set({
        status: {
          connected,
          companyName,
          tallyVersion: data.tally_version ?? null,
          connectedAt: data.connected_at ?? null,
        },
      });
    } catch {
      set({
        status: { connected: false, companyName: null, tallyVersion: null, connectedAt: null },
      });
    }
  },

  startPolling: (clientId: string) => {
    if (pollInterval) clearInterval(pollInterval);
    get().fetchStatus(clientId);
    pollInterval = setInterval(() => get().fetchStatus(clientId), 5000);
    set({ isPolling: true });
  },

  stopPolling: () => {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
    set({ isPolling: false });
  },

  syncLedgers: async (clientId: string) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") || "" : "";
    await fetch(`${TALLY_CONNECTOR_URL}/tally/sync-ledgers/${clientId}?token=${token}`, {
      method: "POST",
    });
  },

  syncItems: async (clientId: string) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") || "" : "";
    await fetch(`${TALLY_CONNECTOR_URL}/tally/sync-items/${clientId}?token=${token}`, {
      method: "POST",
    });
  },
}));
