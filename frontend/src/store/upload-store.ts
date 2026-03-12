import { create } from "zustand";
import api from "@/lib/api";

/**
 * SIZH CA - Upload Store
 * Manages the multi-step bulk upload pipeline state.
 */

const FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || "http://localhost:8001";

export interface UploadJob {
  id: string;
  voucher_type: string;
  bank_account: string;
  original_filename: string;
  file_type: string;
  status: string;
  source_headers: string[] | null;
  field_mapping: Record<string, string> | null;
  row_count: number;
  error_message: string;
  created_at: string;
}

export interface TransactionRow {
  id: string;
  row_number: number;
  raw_data: Record<string, unknown>;
  date: string | null;
  description: string;
  reference: string;
  debit: number;
  credit: number;
  amount: number;
  gst_rate: number;
  cgst: number;
  sgst: number;
  igst: number;
  taxable_amount: number;
  place_of_supply: string;
  assigned_ledger: string | null;
  assigned_ledger_name: string | null;
  ledger_source: string;
  extra_data: Record<string, unknown> | null;
  is_approved: boolean;
  // Gemini-extracted fields
  voucher_type?: string;
  voucher_number?: string;
  narration?: string;
  party_name?: string;
  invoice_no?: string;
  hsn_code?: string;
  ledger_name?: string;
}

type WizardStep = "select" | "upload" | "mapping" | "preview" | "ledger" | "done";

interface UploadState {
  // Wizard state
  step: WizardStep;
  voucherType: string;
  bankAccount: string;
  // Current job
  currentJob: UploadJob | null;
  parsedHeaders: string[];
  previewRows: Record<string, unknown>[];
  totalRows: number;
  fieldMapping: Record<string, string>;
  mappedRows: TransactionRow[];
  // Gemini OCR source flag
  geminiSource: boolean;
  detectedDocType: string;
  // All jobs
  jobs: UploadJob[];
  isLoading: boolean;
  error: string | null;
  // Actions
  setStep: (step: WizardStep) => void;
  setVoucherType: (type: string) => void;
  setBankAccount: (bank: string) => void;
  setFieldMapping: (mapping: Record<string, string>) => void;
  uploadFile: (file: File, voucherType: string) => Promise<void>;
  applyMapping: (clientState: string, clientId: string) => Promise<void>;
  saveRowsAndGenerateVouchers: (clientId: string) => Promise<void>;
  fetchJobs: () => Promise<void>;
  fetchJobRows: (jobId: string) => Promise<TransactionRow[]>;
  assignLedger: (rowIds: string[], ledgerId: string, source?: string) => Promise<void>;
  approveJob: (jobId: string) => Promise<void>;
  reset: () => void;
}

export const useUploadStore = create<UploadState>()((set, get) => ({
  step: "select",
  voucherType: "banking",
  bankAccount: "",
  currentJob: null,
  parsedHeaders: [],
  previewRows: [],
  totalRows: 0,
  fieldMapping: {},
  mappedRows: [],
  geminiSource: false,
  detectedDocType: "",
  jobs: [],
  isLoading: false,
  error: null,

  setStep: (step) => set({ step }),
  setVoucherType: (type) => set({ voucherType: type }),
  setBankAccount: (bank) => set({ bankAccount: bank }),
  setFieldMapping: (mapping) => set({ fieldMapping: mapping }),

  uploadFile: async (file, voucherType) => {
    set({ isLoading: true, error: null });
    try {
      // Step 1: Create job in Django
      const formData = new FormData();
      formData.append("file", file);
      formData.append("voucher_type", voucherType);
      formData.append("bank_account", get().bankAccount);
      const { data: job } = await api.post("/transactions/jobs/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // Step 2: Parse file via FastAPI (auto-detects if Gemini OCR is needed)
      const parseForm = new FormData();
      parseForm.append("file", file);
      parseForm.append("job_id", job.id);
      parseForm.append("voucher_type", voucherType);
      const parseRes = await fetch(`${FASTAPI_URL}/upload/parse`, {
        method: "POST",
        body: parseForm,
      });
      const parsed = await parseRes.json();

      if (!parseRes.ok) throw new Error(parsed.detail || "Parse failed");

      // If Gemini was used, rows come pre-mapped → skip mapping step
      if (parsed.source === "gemini") {
        set({
          currentJob: job,
          parsedHeaders: parsed.headers || [],
          previewRows: parsed.preview || [],
          totalRows: parsed.total_rows || 0,
          mappedRows: (parsed.rows || parsed.preview || []).map(
            (r: Record<string, unknown>, i: number) => ({
              id: `gemini-${i}`,
              row_number: i + 1,
              raw_data: r,
              date: (r.date as string) || null,
              description: (r.description as string) || "",
              reference: (r.reference as string) || "",
              debit: Number(r.debit) || 0,
              credit: Number(r.credit) || 0,
              amount: Number(r.amount) || 0,
              gst_rate: Number(r.gst_rate) || 0,
              cgst: Number(r.cgst) || 0,
              sgst: Number(r.sgst) || 0,
              igst: Number(r.igst) || 0,
              taxable_amount: Number(r.taxable_amount) || 0,
              place_of_supply: (r.place_of_supply as string) || "",
              assigned_ledger: null,
              assigned_ledger_name: null,
              ledger_source: "gemini",
              extra_data: r.extra as Record<string, unknown> | null || null,
              is_approved: false,
              voucher_type: (r.voucher_type as string) || "",
              voucher_number: (r.voucher_number as string) || "",
              narration: (r.description as string) || "",
              party_name: (r.party_name as string) || "",
              invoice_no: (r.invoice_no as string) || "",
              hsn_code: (r.hsn_code as string) || "",
              ledger_name: (r.ledger_name as string) || "",
            })
          ),
          geminiSource: true,
          detectedDocType: parsed.document_type || "",
          step: "preview",  // Skip mapping — AI already extracted fields
          isLoading: false,
        });
      } else {
        // Standard tabular parse — user maps columns manually
        set({
          currentJob: job,
          parsedHeaders: parsed.headers || [],
          previewRows: parsed.preview || [],
          totalRows: parsed.total_rows || 0,
          geminiSource: false,
          detectedDocType: "",
          step: "mapping",
          isLoading: false,
        });
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Upload failed";
      set({ isLoading: false, error: msg });
    }
  },

  applyMapping: async (clientState, clientId) => {
    const { currentJob, fieldMapping, voucherType } = get();
    if (!currentJob) return;
    set({ isLoading: true, error: null });
    try {
      const form = new FormData();
      form.append("job_id", currentJob.id);
      form.append("mapping", JSON.stringify(fieldMapping));
      form.append("voucher_type", voucherType);
      form.append("client_state", clientState);
      form.append("client_id", clientId);
      const res = await fetch(`${FASTAPI_URL}/upload/apply-mapping`, {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Mapping failed");

      // Also save mapping to Django
      await api.post(`/transactions/jobs/${currentJob.id}/field-mapping/`, {
        mapping: fieldMapping,
      });

      set({
        mappedRows: data.rows || [],
        totalRows: data.total_rows || 0,
        step: "preview",
        isLoading: false,
      });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Mapping failed";
      set({ isLoading: false, error: msg });
    }
  },

  /**
   * Persist Gemini/mapped rows from Valkey → Django, then generate Tally vouchers.
   */
  saveRowsAndGenerateVouchers: async (clientId: string) => {
    const { currentJob } = get();
    if (!currentJob) return;
    set({ isLoading: true, error: null });
    try {
      // 1. Ask FastAPI to push rows from Valkey into Django
      const saveRes = await fetch(`${FASTAPI_URL}/upload/save-rows`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: currentJob.id }),
      });
      if (!saveRes.ok) {
        const err = await saveRes.json();
        throw new Error(err.detail || "Save rows failed");
      }

      // 2. Generate Tally vouchers from saved rows
      await api.post(`/transactions/jobs/${currentJob.id}/generate-vouchers/`, {
        client_id: clientId,
      });

      set({ step: "done", isLoading: false });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Save/generate failed";
      set({ isLoading: false, error: msg });
    }
  },

  fetchJobs: async () => {
    set({ isLoading: true });
    try {
      const { data } = await api.get("/transactions/jobs/");
      set({ jobs: data.results || data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchJobRows: async (jobId) => {
    const { data } = await api.get(`/transactions/jobs/${jobId}/rows/`);
    const rows = data.results || data;
    return rows;
  },

  assignLedger: async (rowIds, ledgerId, source = "manual") => {
    await api.post("/transactions/rows/assign-ledger/", {
      row_ids: rowIds,
      ledger_id: ledgerId,
      source,
    });
  },

  approveJob: async (jobId) => {
    await api.post(`/transactions/jobs/${jobId}/approve/`);
  },

  reset: () =>
    set({
      step: "select",
      voucherType: "banking",
      bankAccount: "",
      currentJob: null,
      parsedHeaders: [],
      previewRows: [],
      totalRows: 0,
      fieldMapping: {},
      mappedRows: [],
      geminiSource: false,
      detectedDocType: "",
      error: null,
    }),
}));
