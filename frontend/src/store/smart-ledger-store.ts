import { create } from "zustand";
import api from "@/lib/api";
import axios from "axios";

/**
 * SIZH CA - Smart Ledger Management Store
 * Manages the Suggest → Review → Save flow for client ledger seeding.
 */

export interface LedgerGroup {
  id: string;
  name: string;
  code: string;
  nature: "debit" | "credit";
  description: string;
  display_order: number;
}

export interface LedgerSuggestion {
  name: string;
  group: string;       // group name (display)
  group_id: string;    // UUID for saving
  group_name: string;
  sub_category: string;
  is_custom: boolean;
}

export interface ClientLedger {
  id: string;
  name: string;
  group: string;
  group_name: string;
  group_code: string;
  sub_category: string;
  opening_balance: number;
  is_custom: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface LedgerSummary {
  industry_type: string;
  total_count: number;
  by_group: Record<string, number>;
  industry_specific_count: number;
}

interface SmartLedgerState {
  // Data
  groups: LedgerGroup[];
  suggestions: LedgerSuggestion[];
  summary: LedgerSummary | null;
  clientLedgers: ClientLedger[];
  availableIndustries: string[];

  // Editing state (the CA reviews & edits before saving)
  editableLedgers: LedgerSuggestion[];

  // UI state
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  saveResult: { created: number; updated: number; total_client_ledgers: number } | null;

  // Actions
  fetchGroups: () => Promise<void>;
  fetchSuggestions: (industryType: string) => Promise<void>;
  fetchClientLedgers: (params?: Record<string, string>) => Promise<void>;

  // Editing actions
  setEditableLedgers: (ledgers: LedgerSuggestion[]) => void;
  addCustomLedger: (name: string, groupId: string, groupName: string) => void;
  removeLedger: (index: number) => void;
  updateLedgerName: (index: number, newName: string) => void;
  updateLedgerGroup: (index: number, groupId: string, groupName: string) => void;

  // Save
  bulkSaveLedgers: () => Promise<void>;
  reset: () => void;
}

export const useSmartLedgerStore = create<SmartLedgerState>()((set, get) => ({
  groups: [],
  suggestions: [],
  summary: null,
  clientLedgers: [],
  availableIndustries: [],
  editableLedgers: [],
  isLoading: false,
  isSaving: false,
  error: null,
  saveResult: null,

  fetchGroups: async () => {
    try {
      const { data } = await api.get("/masters/ledger-groups/");
      const results = data.results || data;
      set({ groups: results });
    } catch {
      // non-critical
    }
  },

  fetchSuggestions: async (industryType: string) => {
    set({ isLoading: true, error: null, saveResult: null });
    try {
      const { data } = await api.get("/masters/ledger-suggest/", {
        params: { industry_type: industryType },
      });
      const suggestions = data.suggestions || [];
      set({
        suggestions,
        summary: data.summary || null,
        availableIndustries: data.available_industries || [],
        editableLedgers: suggestions.map((s: LedgerSuggestion) => ({ ...s })),
        isLoading: false,
      });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to fetch suggestions";
      set({ isLoading: false, error: msg });
    }
  },

  fetchClientLedgers: async (params) => {
    set({ isLoading: true });
    try {
      const { data } = await api.get("/masters/client-ledgers/", { params });
      const results = data.results || data;
      set({ clientLedgers: results, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  setEditableLedgers: (ledgers) => set({ editableLedgers: ledgers }),

  addCustomLedger: (name, groupId, groupName) => {
    const { editableLedgers } = get();
    set({
      editableLedgers: [
        ...editableLedgers,
        {
          name,
          group: groupName,
          group_id: groupId,
          group_name: groupName,
          sub_category: "Custom",
          is_custom: true,
        },
      ],
    });
  },

  removeLedger: (index) => {
    const { editableLedgers } = get();
    set({
      editableLedgers: editableLedgers.filter((_, i) => i !== index),
    });
  },

  updateLedgerName: (index, newName) => {
    const { editableLedgers } = get();
    const next = [...editableLedgers];
    next[index] = { ...next[index], name: newName };
    set({ editableLedgers: next });
  },

  updateLedgerGroup: (index, groupId, groupName) => {
    const { editableLedgers } = get();
    const next = [...editableLedgers];
    next[index] = { ...next[index], group_id: groupId, group_name: groupName, group: groupName };
    set({ editableLedgers: next });
  },

  bulkSaveLedgers: async () => {
    const { editableLedgers } = get();
    if (!editableLedgers.length) return;

    set({ isSaving: true, error: null });
    try {
      const payload = {
        ledgers: editableLedgers.map((l) => ({
          name: l.name,
          group: l.group_id,
          sub_category: l.sub_category || "",
          is_custom: l.is_custom || false,
          opening_balance: 0,
        })),
      };
      const { data } = await api.post("/masters/client-ledgers/bulk-save/", payload);
      set({
        isSaving: false,
        saveResult: {
          created: data.created,
          updated: data.updated,
          total_client_ledgers: data.total_client_ledgers,
        },
      });
    } catch (e: unknown) {
      let msg = e instanceof Error ? e.message : "Save failed";
      if (axios.isAxiosError(e)) {
        const payload = e.response?.data;
        if (typeof payload === "string") {
          msg = payload;
        } else if (payload?.error && typeof payload.error === "string") {
          msg = payload.error;
        } else if (payload?.detail && typeof payload.detail === "string") {
          msg = payload.detail;
        } else if (payload && typeof payload === "object") {
          const firstKey = Object.keys(payload)[0];
          const firstValue = firstKey ? payload[firstKey as keyof typeof payload] : null;
          if (Array.isArray(firstValue) && firstValue.length > 0) {
            msg = `${firstKey}: ${String(firstValue[0])}`;
          } else if (typeof firstValue === "string") {
            msg = `${firstKey}: ${firstValue}`;
          }
        }
      }
      set({ isSaving: false, error: msg });
    }
  },

  reset: () =>
    set({
      suggestions: [],
      summary: null,
      editableLedgers: [],
      error: null,
      saveResult: null,
    }),
}));
