"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useUploadStore, type TransactionRow } from "@/store/upload-store";
import { useMastersStore, type TallyLedger } from "@/store/masters-store";
import { useClientStore } from "@/store/client-store";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileSpreadsheet,
  ArrowRight,
  ArrowLeft,
  Check,
  CheckCircle2,
  Columns3,
  Eye,
  BookOpen,
  Send,
  ChevronDown,
  RefreshCw,
  X,
  AlertCircle,
  Landmark,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ─── Constants ─── */
const VOUCHER_TYPES = [
  { value: "banking", label: "Banking", icon: Landmark, color: "blue" },
  { value: "sales", label: "Sales", icon: FileSpreadsheet, color: "green" },
  { value: "purchase", label: "Purchase", icon: FileSpreadsheet, color: "orange" },
  { value: "sales_return", label: "Sales Return", icon: FileSpreadsheet, color: "teal" },
  { value: "purchase_return", label: "Purchase Return", icon: FileSpreadsheet, color: "rose" },
  { value: "journal", label: "Journal", icon: BookOpen, color: "purple" },
  { value: "ledger", label: "Ledger", icon: BookOpen, color: "indigo" },
  { value: "items", label: "Items", icon: BookOpen, color: "cyan" },
] as const;

const WIZARD_STEPS = [
  { key: "select", label: "Select Type" },
  { key: "upload", label: "Upload File" },
  { key: "mapping", label: "Field Mapping" },
  { key: "preview", label: "Preview" },
  { key: "ledger", label: "Assign Ledgers" },
  { key: "done", label: "Complete" },
] as const;

const TARGET_FIELDS: Record<string, string[]> = {
  banking: ["date", "description", "reference", "debit", "credit"],
  sales: ["date", "invoice_no", "party_name", "amount", "gst_rate", "place_of_supply"],
  purchase: ["date", "invoice_no", "party_name", "amount", "gst_rate", "place_of_supply"],
  sales_return: ["date", "invoice_no", "party_name", "amount", "gst_rate"],
  purchase_return: ["date", "invoice_no", "party_name", "amount", "gst_rate"],
  journal: ["date", "description", "debit", "credit"],
  ledger: ["name", "group", "opening_balance"],
  items: ["name", "group", "hsn_code", "uom", "gst_rate", "opening_stock", "opening_value"],
};

/* ─── Step indicator ─── */
function StepIndicator({ currentIdx }: { currentIdx: number }) {
  return (
    <div className="flex items-center gap-1">
      {WIZARD_STEPS.map((s, i) => (
        <div key={s.key} className="flex items-center gap-1">
          <div
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition-colors",
              i < currentIdx
                ? "bg-green-100 text-green-700"
                : i === currentIdx
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-400"
            )}
          >
            {i < currentIdx ? <Check className="h-3.5 w-3.5" /> : i + 1}
          </div>
          <span
            className={cn(
              "hidden lg:inline text-xs font-medium",
              i === currentIdx ? "text-blue-700" : "text-gray-400"
            )}
          >
            {s.label}
          </span>
          {i < WIZARD_STEPS.length - 1 && (
            <div
              className={cn(
                "mx-1 h-px w-6",
                i < currentIdx ? "bg-green-300" : "bg-gray-200"
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}

/* ────────── Step 1: Select Voucher Type ────────── */
function StepSelect() {
  const { voucherType, setVoucherType, bankAccount, setBankAccount, setStep } = useUploadStore();

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-800">Select Voucher Type</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {VOUCHER_TYPES.map((vt) => {
          const Icon = vt.icon;
          const selected = voucherType === vt.value;
          return (
            <button
              key={vt.value}
              onClick={() => setVoucherType(vt.value)}
              className={cn(
                "flex flex-col items-center gap-2 rounded-xl border-2 p-5 text-sm font-medium transition-all",
                selected
                  ? "border-blue-500 bg-blue-50 text-blue-700 shadow-sm"
                  : "border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50"
              )}
            >
              <Icon className="h-6 w-6" />
              {vt.label}
            </button>
          );
        })}
      </div>

      {voucherType === "banking" && (
        <div className="max-w-sm">
          <label className="block text-xs font-medium text-gray-600 mb-1">Bank Account Name</label>
          <input
            type="text"
            value={bankAccount}
            onChange={(e) => setBankAccount(e.target.value)}
            placeholder="e.g. HDFC Bank – Current A/c"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>
      )}

      <button
        onClick={() => setStep("upload")}
        disabled={!voucherType}
        className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        Next
        <ArrowRight className="h-4 w-4" />
      </button>
    </div>
  );
}

/* ────────── Step 2: File Upload ────────── */
function StepUpload() {
  const { voucherType, uploadFile, setStep, isLoading, error } = useUploadStore();

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) {
        uploadFile(accepted[0], voucherType);
      }
    },
    [voucherType, uploadFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "application/pdf": [".pdf"],
      "image/*": [".jpg", ".jpeg", ".png"],
    },
    maxFiles: 1,
    disabled: isLoading,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">Upload File</h2>
        <button
          onClick={() => setStep("select")}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>
      </div>

      <div
        {...getRootProps()}
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors cursor-pointer",
          isDragActive
            ? "border-blue-400 bg-blue-50"
            : "border-gray-300 bg-gray-50 hover:border-gray-400"
        )}
      >
        <input {...getInputProps()} />
        {isLoading ? (
          <>
            <RefreshCw className="h-10 w-10 animate-spin text-blue-500" />
            <p className="mt-4 text-sm text-gray-600">Parsing file…</p>
          </>
        ) : (
          <>
            <Upload className="h-10 w-10 text-gray-400" />
            <p className="mt-4 text-sm font-medium text-gray-700">
              Drag & drop your file here, or click to browse
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Supports Excel (.xlsx/.xls), CSV, PDF, and images (JPG/PNG)
            </p>
          </>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
}

/* ────────── Searchable Tally Field Combobox ────────── */
function FieldCombobox({
  value,
  options,
  onChange,
}: {
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(value);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => { setQuery(value ? value.replace(/_/g, " ") : ""); }, [value]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const filtered = options.filter((o) =>
    o.replace(/_/g, " ").toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div ref={ref} className="relative w-full">
      <div className={cn(
        "flex items-center rounded-lg border bg-white transition-colors",
        open ? "border-blue-500 ring-1 ring-blue-200" : "border-gray-300"
      )}>
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          placeholder="Select or type Tally field…"
          className="flex-1 bg-transparent px-3 py-1.5 text-xs outline-none placeholder-gray-400"
        />
        {value && (
          <button
            onMouseDown={(e) => { e.preventDefault(); onChange(""); setQuery(""); }}
            className="pr-2 text-gray-400 hover:text-red-500"
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>
      {open && filtered.length > 0 && (
        <ul className="absolute z-50 mt-1 max-h-44 w-full overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
          {filtered.map((opt) => (
            <li
              key={opt}
              onMouseDown={(e) => {
                e.preventDefault();
                onChange(opt);
                setQuery(opt.replace(/_/g, " "));
                setOpen(false);
              }}
              className={cn(
                "cursor-pointer px-3 py-2 text-xs hover:bg-blue-50 capitalize",
                value === opt && "bg-blue-50 text-blue-700 font-semibold"
              )}
            >
              {opt.replace(/_/g, " ")}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ────────── Step 3: Field Mapping ────────── */
function StepMapping() {
  const {
    parsedHeaders,
    previewRows,
    voucherType,
    fieldMapping,
    setFieldMapping,
    applyMapping,
    setStep,
    isLoading,
    error,
  } = useUploadStore();
  const { activeClient } = useClientStore();
  const tallyFields = TARGET_FIELDS[voucherType] || TARGET_FIELDS.banking;

  // headerToTally: sheetHeader → tallyField (inverse of store format)
  const [headerToTally, setHeaderToTally] = useState<Record<string, string>>(() => {
    const inv: Record<string, string> = {};
    Object.entries(fieldMapping || {}).forEach(([tally, header]) => {
      if (header) inv[header] = tally;
    });
    return inv;
  });

  const handleAssign = (header: string, tallyField: string) => {
    setHeaderToTally((prev) => {
      const next = { ...prev };
      // Remove any prior assignment of this tally field to a different header
      Object.keys(next).forEach((h) => { if (next[h] === tallyField && h !== header) delete next[h]; });
      if (tallyField) next[header] = tallyField;
      else delete next[header];
      return next;
    });
  };

  // Sample values: first 3 non-empty cells from this column
  const getSample = (header: string): string => {
    return (
      previewRows
        .map((r) => r[header])
        .filter(Boolean)
        .slice(0, 3)
        .join(" , ") || "—"
    );
  };

  const mapped = parsedHeaders.filter((h) => !!headerToTally[h]);
  const unmapped = parsedHeaders.filter((h) => !headerToTally[h]);

  const handleApply = async () => {
    const mapping: Record<string, string> = {};
    Object.entries(headerToTally).forEach(([header, tally]) => {
      if (tally) mapping[tally] = header;
    });
    setFieldMapping(mapping);
    if (activeClient) {
      await applyMapping(activeClient.state || "", activeClient.id);
    }
  };

  const MappingPanel = ({
    headers,
    title,
    badge,
    accentClass,
  }: {
    headers: string[];
    title: string;
    badge: number;
    accentClass: string;
  }) => (
    <div className={cn("flex-1 min-w-0 rounded-xl border-2 bg-white overflow-hidden", accentClass)}>
      {/* Panel header */}
      <div className="flex items-center gap-2 border-b border-gray-100 bg-gray-50 px-4 py-2.5">
        <span className="text-sm font-semibold text-gray-800">{title}</span>
        <span className={cn(
          "rounded-full px-2 py-0.5 text-xs font-bold text-white",
          title === "Mapped" ? "bg-green-500" : "bg-gray-400"
        )}>
          {badge}
        </span>
      </div>
      {/* Column labels */}
      <div className="grid grid-cols-[1fr_1.2fr_1fr] gap-2 border-b border-gray-100 bg-gray-50 px-4 py-2 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
        <span>Your Sheet Header</span>
        <span>Tally Fields</span>
        <span>Your Sheet Data</span>
      </div>
      {/* Rows */}
      <div className="divide-y divide-gray-50 max-h-80 overflow-y-auto">
        {headers.length === 0 ? (
          <p className="px-4 py-8 text-center text-xs text-gray-400">
            {title === "Mapped" ? "No columns mapped yet. Start mapping below →" : "All columns are mapped!"}
          </p>
        ) : (
          headers.map((header) => (
            <div key={header} className="grid grid-cols-[1fr_1.2fr_1fr] gap-2 items-center px-4 py-2">
              <span className="text-xs font-medium text-gray-800 truncate" title={header}>
                {header}
              </span>
              <FieldCombobox
                value={headerToTally[header] || ""}
                options={tallyFields}
                onChange={(v) => handleAssign(header, v)}
              />
              <span className="text-xs text-gray-500 truncate" title={getSample(header)}>
                {getSample(header)}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Map Fields</h2>
          <p className="text-sm text-gray-500">
            Match each column from your uploaded file to the correct Tally field.
          </p>
        </div>
        <button
          onClick={() => setStep("upload")}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>
      </div>

      {parsedHeaders.length === 0 ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-6 text-center text-sm text-amber-800">
          No column headers detected. Please go back and re-upload your file.
        </div>
      ) : (
        <div className="flex gap-4">
          <MappingPanel
            headers={mapped}
            title="Mapped"
            badge={mapped.length}
            accentClass="border-green-300"
          />
          <MappingPanel
            headers={unmapped}
            title="Unmapped"
            badge={unmapped.length}
            accentClass="border-gray-200"
          />
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      <button
        onClick={handleApply}
        disabled={isLoading || mapped.length === 0}
        className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {isLoading ? (
          <>
            <RefreshCw className="h-4 w-4 animate-spin" />
            Applying…
          </>
        ) : (
          <>
            <Columns3 className="h-4 w-4" />
            Apply Mapping ({mapped.length} fields mapped)
          </>
        )}
      </button>
    </div>
  );
}

/* ────────── Step 4: Preview ────────── */
function StepPreview() {
  const { mappedRows, totalRows, setStep, voucherType, geminiSource, detectedDocType, currentJob, saveRowsAndGenerateVouchers, isLoading } = useUploadStore();
  const { activeClient } = useClientStore();
  const showGST = ["sales", "purchase", "sales_return", "purchase_return"].includes(voucherType);

  const handleSaveAndGenerate = async () => {
    if (activeClient) {
      await saveRowsAndGenerateVouchers(activeClient.id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">AI Preview</h2>
          <p className="text-sm text-gray-500">
            {totalRows} rows mapped • Review and proceed to ledger assignment.
          </p>
          {geminiSource && (
            <div className="mt-1 flex items-center gap-2">
              <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                Gemini AI Extracted
              </span>
              {detectedDocType && (
                <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                  {detectedDocType}
                </span>
              )}
            </div>
          )}
        </div>
        <button
          onClick={() => setStep(geminiSource ? "upload" : "mapping")}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 text-left text-[11px] font-semibold uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-3 py-2">#</th>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">Description</th>
              {geminiSource && <th className="px-3 py-2">Party</th>}
              {geminiSource && <th className="px-3 py-2">Invoice No</th>}
              <th className="px-3 py-2">Reference</th>
              <th className="px-3 py-2 text-right">Debit</th>
              <th className="px-3 py-2 text-right">Credit</th>
              {showGST && <th className="px-3 py-2 text-right">CGST</th>}
              {showGST && <th className="px-3 py-2 text-right">SGST</th>}
              {showGST && <th className="px-3 py-2 text-right">IGST</th>}
              <th className="px-3 py-2">Ledger</th>
              <th className="px-3 py-2">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {mappedRows.slice(0, 50).map((row, i) => (
              <tr key={row.id || i} className="hover:bg-gray-50">
                <td className="px-3 py-2 text-gray-400">{row.row_number || i + 1}</td>
                <td className="px-3 py-2">{row.date || "—"}</td>
                <td className="px-3 py-2 max-w-[200px] truncate">{row.description || "—"}</td>
                {geminiSource && (
                  <td className="px-3 py-2 max-w-[140px] truncate">{row.party_name || "—"}</td>
                )}
                {geminiSource && (
                  <td className="px-3 py-2">{row.invoice_no || "—"}</td>
                )}
                <td className="px-3 py-2">{row.reference || "—"}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {row.debit ? row.debit.toLocaleString("en-IN") : "—"}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {row.credit ? row.credit.toLocaleString("en-IN") : "—"}
                </td>
                {showGST && (
                  <td className="px-3 py-2 text-right tabular-nums">
                    {row.cgst ? row.cgst.toFixed(2) : "—"}
                  </td>
                )}
                {showGST && (
                  <td className="px-3 py-2 text-right tabular-nums">
                    {row.sgst ? row.sgst.toFixed(2) : "—"}
                  </td>
                )}
                {showGST && (
                  <td className="px-3 py-2 text-right tabular-nums">
                    {row.igst ? row.igst.toFixed(2) : "—"}
                  </td>
                )}
                <td className="px-3 py-2">
                  {(row.assigned_ledger_name || row.ledger_name) ? (
                    <span className="rounded bg-green-50 px-2 py-0.5 text-green-700">
                      {row.assigned_ledger_name || row.ledger_name}
                    </span>
                  ) : (
                    <span className="text-gray-400">Unassigned</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={cn(
                      "rounded px-2 py-0.5 text-[10px] font-semibold uppercase",
                      row.ledger_source === "rule"
                        ? "bg-purple-50 text-purple-700"
                        : row.ledger_source === "ai"
                        ? "bg-amber-50 text-amber-700"
                        : row.ledger_source === "gemini"
                        ? "bg-emerald-50 text-emerald-700"
                        : row.ledger_source === "manual"
                        ? "bg-blue-50 text-blue-700"
                        : "bg-gray-100 text-gray-400"
                    )}
                  >
                    {row.ledger_source || "—"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {mappedRows.length > 50 && (
        <p className="text-xs text-gray-400 text-center">
          Showing 50 of {mappedRows.length} rows in preview.
        </p>
      )}

      <div className="flex items-center gap-3">
        <button
          onClick={() => setStep("ledger")}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          <ArrowRight className="h-4 w-4" />
          Proceed to Ledger Assignment
        </button>
        {geminiSource && (
          <button
            onClick={handleSaveAndGenerate}
            disabled={isLoading}
            className="flex items-center gap-2 rounded-lg bg-green-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {isLoading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Generating…
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                Save & Generate Vouchers
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

/* ────────── Step 5: Ledger Assignment ────────── */
function StepLedger() {
  const { mappedRows, currentJob, assignLedger, approveJob, setStep, isLoading } = useUploadStore();
  const { ledgers, fetchLedgers } = useMastersStore();
  const [assignments, setAssignments] = useState<Record<string, string>>({});
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [bulkLedger, setBulkLedger] = useState("");

  useEffect(() => {
    fetchLedgers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Initialise assignments from mapped rows
  useEffect(() => {
    const init: Record<string, string> = {};
    mappedRows.forEach((r) => {
      if (r.assigned_ledger) init[r.id] = r.assigned_ledger;
    });
    setAssignments(init);
  }, [mappedRows]);

  const toggleRow = (id: string) => {
    setSelectedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedRows.size === mappedRows.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(mappedRows.map((r) => r.id)));
    }
  };

  const handleAssignSingle = async (rowId: string, ledgerId: string) => {
    setAssignments((prev) => ({ ...prev, [rowId]: ledgerId }));
    await assignLedger([rowId], ledgerId, "manual");
  };

  const handleBulkAssign = async () => {
    if (!bulkLedger || selectedRows.size === 0) return;
    const ids = Array.from(selectedRows);
    await assignLedger(ids, bulkLedger, "manual");
    const next: Record<string, string> = { ...assignments };
    ids.forEach((id) => (next[id] = bulkLedger));
    setAssignments(next);
    setSelectedRows(new Set());
  };

  const handleApprove = async () => {
    if (!currentJob) return;
    await approveJob(currentJob.id);
    setStep("done");
  };

  const unassignedCount = mappedRows.filter(
    (r) => !assignments[r.id] && !r.assigned_ledger
  ).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Assign Ledgers</h2>
          <p className="text-sm text-gray-500">
            {unassignedCount} of {mappedRows.length} rows unassigned
          </p>
        </div>
        <button
          onClick={() => setStep("preview")}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>
      </div>

      {/* Bulk assign bar */}
      <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <input
          type="checkbox"
          checked={selectedRows.size === mappedRows.length && mappedRows.length > 0}
          onChange={toggleAll}
          className="h-4 w-4 rounded border-gray-300 text-blue-600"
        />
        <span className="text-xs text-gray-500">{selectedRows.size} selected</span>
        <select
          value={bulkLedger}
          onChange={(e) => setBulkLedger(e.target.value)}
          className="ml-auto rounded-lg border border-gray-300 px-3 py-1.5 text-sm outline-none focus:border-blue-500"
        >
          <option value="">Bulk assign to…</option>
          {ledgers.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name}
            </option>
          ))}
        </select>
        <button
          onClick={handleBulkAssign}
          disabled={!bulkLedger || selectedRows.size === 0}
          className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          Assign
        </button>
      </div>

      {/* Rows table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 max-h-[500px] overflow-y-auto">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-gray-50 text-left text-[11px] font-semibold uppercase tracking-wider text-gray-500">
            <tr>
              <th className="px-3 py-2 w-8"></th>
              <th className="px-3 py-2">#</th>
              <th className="px-3 py-2">Description</th>
              <th className="px-3 py-2 text-right">Amount</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2 w-64">Ledger</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {mappedRows.map((row, i) => (
              <tr key={row.id || i} className="hover:bg-gray-50">
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    checked={selectedRows.has(row.id)}
                    onChange={() => toggleRow(row.id)}
                    className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600"
                  />
                </td>
                <td className="px-3 py-2 text-gray-400">{row.row_number || i + 1}</td>
                <td className="px-3 py-2 max-w-[250px] truncate">{row.description || "—"}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {(row.debit || row.credit || row.amount || 0).toLocaleString("en-IN")}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={cn(
                      "rounded px-2 py-0.5 text-[10px] font-semibold uppercase",
                      row.ledger_source === "rule"
                        ? "bg-purple-50 text-purple-700"
                        : row.ledger_source === "ai"
                        ? "bg-amber-50 text-amber-700"
                        : "bg-blue-50 text-blue-700"
                    )}
                  >
                    {row.ledger_source || "manual"}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <select
                    value={assignments[row.id] || row.assigned_ledger || ""}
                    onChange={(e) => handleAssignSingle(row.id, e.target.value)}
                    className={cn(
                      "w-full rounded border px-2 py-1 text-xs outline-none",
                      assignments[row.id] || row.assigned_ledger
                        ? "border-green-300 bg-green-50"
                        : "border-gray-300"
                    )}
                  >
                    <option value="">— select ledger —</option>
                    {ledgers.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={handleApprove}
          disabled={isLoading || unassignedCount > 0}
          className="flex items-center gap-2 rounded-lg bg-green-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          <Send className="h-4 w-4" />
          Approve & Send to Tally
        </button>
        {unassignedCount > 0 && (
          <span className="text-xs text-amber-600">
            Assign all rows before approving.
          </span>
        )}
      </div>
    </div>
  );
}

/* ────────── Step 6: Done ────────── */
function StepDone() {
  const { currentJob, reset } = useUploadStore();

  return (
    <div className="flex flex-col items-center justify-center py-16 space-y-4">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
        <CheckCircle2 className="h-8 w-8 text-green-600" />
      </div>
      <h2 className="text-xl font-bold text-gray-900">Upload Complete!</h2>
      <p className="text-sm text-gray-500 max-w-md text-center">
        Job <span className="font-mono text-gray-700">{currentJob?.id?.slice(0, 8)}…</span> has
        been approved and queued for Tally. You can track status in the Transactions page.
      </p>
      <button
        onClick={reset}
        className="mt-4 flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
      >
        <Upload className="h-4 w-4" />
        Upload Another
      </button>
    </div>
  );
}

/* ────── MAIN PAGE ────── */
export default function BulkUploadPage() {
  const { step } = useUploadStore();
  const stepIdx = WIZARD_STEPS.findIndex((s) => s.key === step);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
          <Upload className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bulk Upload</h1>
          <p className="text-sm text-gray-500">
            Upload Excel, CSV, PDF, or images — AI-powered mapping & ledger assignment.
          </p>
        </div>
      </div>

      {/* Step Indicator */}
      <StepIndicator currentIdx={stepIdx} />

      {/* Step Content */}
      <div className="rounded-xl border border-gray-200 bg-white p-6">
        {step === "select" && <StepSelect />}
        {step === "upload" && <StepUpload />}
        {step === "mapping" && <StepMapping />}
        {step === "preview" && <StepPreview />}
        {step === "ledger" && <StepLedger />}
        {step === "done" && <StepDone />}
      </div>
    </div>
  );
}
