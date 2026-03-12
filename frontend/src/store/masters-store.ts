import { create } from "zustand";
import api from "@/lib/api";

/**
 * SIZH CA - Masters Store
 * Manages Tally Ledgers, Items, and Rules data.
 */

export interface TallyLedger {
  id: string;
  name: string;
  alias: string;
  group: string;
  parent_group: string;
  tax_category: string;
  gstin: string;
  gst_registration_type: string;
  state: string;
  opening_balance: number;
  closing_balance: number;
  is_active: boolean;
  synced_at: string;
}

export interface TallyItem {
  id: string;
  name: string;
  alias: string;
  group: string;
  category: string;
  uom: string;
  hsn_code: string;
  gst_rate: number;
  opening_stock: number;
  opening_value: number;
  is_active: boolean;
  synced_at: string;
}

export interface Rule {
  id: string;
  description: string;
  rule_type: string;
  from_field: string;
  to_field: string;
  target_ledger: string | null;
  target_ledger_name: string | null;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
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
}

interface MastersState {
  ledgers: TallyLedger[];
  items: TallyItem[];
  rules: Rule[];
  clientLedgers: ClientLedger[];
  ledgerCount: number;
  itemCount: number;
  ruleCount: number;
  clientLedgerCount: number;
  isLoading: boolean;
  fetchLedgers: (params?: Record<string, string>) => Promise<void>;
  fetchItems: (params?: Record<string, string>) => Promise<void>;
  fetchRules: (params?: Record<string, string>) => Promise<void>;
  fetchClientLedgers: (params?: Record<string, string>) => Promise<void>;
  createRule: (data: Partial<Rule>) => Promise<Rule>;
  updateRule: (id: string, data: Partial<Rule>) => Promise<Rule>;
  deleteRule: (id: string) => Promise<void>;
}

export const useMastersStore = create<MastersState>()((set, get) => ({
  ledgers: [],
  items: [],
  rules: [],
  clientLedgers: [],
  ledgerCount: 0,
  itemCount: 0,
  ruleCount: 0,
  clientLedgerCount: 0,
  isLoading: false,

  fetchLedgers: async (params) => {
    set({ isLoading: true });
    try {
      const { data } = await api.get("/masters/ledgers/", { params });
      const results = data.results || data;
      set({ ledgers: results, ledgerCount: data.count ?? results.length, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchItems: async (params) => {
    set({ isLoading: true });
    try {
      const { data } = await api.get("/masters/items/", { params });
      const results = data.results || data;
      set({ items: results, itemCount: data.count ?? results.length, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchRules: async (params) => {
    set({ isLoading: true });
    try {
      const { data } = await api.get("/masters/rules/", { params });
      const results = data.results || data;
      set({ rules: results, ruleCount: data.count ?? results.length, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchClientLedgers: async (params) => {
    set({ isLoading: true });
    try {
      const { data } = await api.get("/masters/client-ledgers/", { params });
      const results = data.results || data;
      set({ clientLedgers: results, clientLedgerCount: data.count ?? results.length, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  createRule: async (ruleData) => {
    const { data } = await api.post("/masters/rules/", ruleData);
    set({ rules: [...get().rules, data] });
    return data;
  },

  updateRule: async (id, ruleData) => {
    const { data } = await api.patch(`/masters/rules/${id}/`, ruleData);
    set({ rules: get().rules.map((r) => (r.id === id ? data : r)) });
    return data;
  },

  deleteRule: async (id) => {
    await api.delete(`/masters/rules/${id}/`);
    set({ rules: get().rules.filter((r) => r.id !== id) });
  },
}));
