import { create } from "zustand";
import api from "@/lib/api";

/**
 * SIZH CA - Tally Connection Store
 * Tracks real-time Tally ERP/Prime connection status.
 */

const FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || "http://localhost:8001";

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
    try {
      const res = await fetch(`${FASTAPI_URL}/tally/status/${clientId}`);
      const data = await res.json();
      set({
        status: {
          connected: data.connected ?? false,
          companyName: data.company_name ?? null,
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
    await fetch(`${FASTAPI_URL}/tally/sync-ledgers/${clientId}?token=${token}`, {
      method: "POST",
    });
  },

  syncItems: async (clientId: string) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") || "" : "";
    await fetch(`${FASTAPI_URL}/tally/sync-items/${clientId}?token=${token}`, {
      method: "POST",
    });
  },
}));
