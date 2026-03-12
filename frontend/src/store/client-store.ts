import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "@/lib/api";

/**
 * SIZH CA - Client Profile Store (Zustand)
 * Manages the active client profile and list of all client profiles.
 * The selected client ID is persisted and synced with the backend session.
 */

export interface ClientProfile {
  id: string;
  name: string;
  trade_name: string | null;
  pan: string | null;
  gstin: string | null;
  gst_type: string;
  industry_type: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  state: string | null;
  pincode: string | null;
  financial_year_start: string | null;
  tally_company_name: string | null;
  created_at: string;
  updated_at: string;
}

interface ClientState {
  clients: ClientProfile[];
  activeClient: ClientProfile | null;
  isLoading: boolean;
  fetchClients: () => Promise<void>;
  fetchActiveClient: () => Promise<void>;
  switchClient: (clientId: string) => Promise<void>;
  createClient: (data: Partial<ClientProfile>) => Promise<ClientProfile>;
}

export const useClientStore = create<ClientState>()(
  persist(
    (set, get) => ({
      clients: [],
      activeClient: null,
      isLoading: false,

      fetchClients: async () => {
        set({ isLoading: true });
        try {
          const { data } = await api.get("/clients/");
          set({ clients: data.results || data, isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      fetchActiveClient: async () => {
        try {
          const { data } = await api.get("/clients/active/");
          set({ activeClient: data.active_client });
        } catch {
          set({ activeClient: null });
        }
      },

      switchClient: async (clientId) => {
        try {
          const { data } = await api.post("/clients/switch/", {
            client_profile_id: clientId,
          });
          set({ activeClient: data.active_client });
        } catch (error) {
          throw error;
        }
      },

      createClient: async (clientData) => {
        const { data } = await api.post("/clients/", clientData);
        const { clients } = get();
        set({ clients: [...clients, data] });
        return data;
      },
    }),
    {
      name: "sizh-ca-client",
      partialize: (state) => ({
        activeClient: state.activeClient,
      }),
    }
  )
);
