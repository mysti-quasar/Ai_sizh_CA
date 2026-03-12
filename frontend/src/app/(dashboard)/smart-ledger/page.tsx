"use client";

import { useEffect, useState, useMemo, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  useSmartLedgerStore,
  type LedgerSuggestion,
  type LedgerGroup,
} from "@/store/smart-ledger-store";
import { useClientStore } from "@/store/client-store";
import {
  BookOpen,
  Sparkles,
  Search,
  Plus,
  Trash2,
  Save,
  CheckCircle2,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  AlertCircle,
  Building2,
  ShoppingCart,
  Briefcase,
  Monitor,
  Factory,
  X,
  LayoutDashboard,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ─── Industry card config ─── */
const INDUSTRY_CARDS: {
  key: string;
  label: string;
  icon: React.ElementType;
  description: string;
  color: string;
  bg: string;
}[] = [
  {
    key: "trading",
    label: "Trading",
    icon: ShoppingCart,
    description: "Buy & sell goods, wholesalers, retailers",
    color: "text-emerald-700",
    bg: "bg-emerald-50 border-emerald-200 hover:border-emerald-400",
  },
  {
    key: "service",
    label: "Service",
    icon: Briefcase,
    description: "Consulting, professional services, freelancers",
    color: "text-blue-700",
    bg: "bg-blue-50 border-blue-200 hover:border-blue-400",
  },
  {
    key: "ecommerce",
    label: "E-Commerce",
    icon: Monitor,
    description: "Amazon, Flipkart sellers, online retail",
    color: "text-purple-700",
    bg: "bg-purple-50 border-purple-200 hover:border-purple-400",
  },
  {
    key: "manufacturing",
    label: "Manufacturing",
    icon: Factory,
    description: "Production, assembly, raw material processing",
    color: "text-orange-700",
    bg: "bg-orange-50 border-orange-200 hover:border-orange-400",
  },
];

/* ─── Step indicator ─── */
function StepIndicator({ step }: { step: number }) {
  const steps = [
    { num: 1, label: "Select Industry" },
    { num: 2, label: "Review Ledgers" },
    { num: 3, label: "Save & Confirm" },
  ];
  return (
    <div className="flex items-center gap-2">
      {steps.map((s, idx) => (
        <div key={s.num} className="flex items-center gap-2">
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold transition-colors",
              step === s.num
                ? "bg-blue-600 text-white"
                : step > s.num
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-400"
            )}
          >
            {step > s.num ? <CheckCircle2 className="h-4 w-4" /> : s.num}
          </div>
          <span
            className={cn(
              "text-sm font-medium hidden sm:inline",
              step === s.num ? "text-gray-900" : "text-gray-400"
            )}
          >
            {s.label}
          </span>
          {idx < steps.length - 1 && (
            <ChevronRight className="h-4 w-4 text-gray-300" />
          )}
        </div>
      ))}
    </div>
  );
}

/* ─── Add custom ledger modal ─── */
function AddLedgerModal({
  open,
  groups,
  onAdd,
  onClose,
}: {
  open: boolean;
  groups: LedgerGroup[];
  onAdd: (name: string, groupId: string, groupName: string) => void;
  onClose: () => void;
}) {
  const [name, setName] = useState("");
  const [groupId, setGroupId] = useState("");

  if (!open) return null;

  const selectedGroup = groups.find((g) => g.id === groupId);

  const handleSubmit = () => {
    if (!name.trim() || !groupId) return;
    onAdd(name.trim(), groupId, selectedGroup?.name || "");
    setName("");
    setGroupId("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Add Custom Ledger</h3>
          <button onClick={onClose} className="rounded p-1 hover:bg-gray-100">
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ledger Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Director Salary, Loan from HDFC"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ledger Group</label>
            <select
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            >
              <option value="">Select a group…</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} ({g.nature})
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!name.trim() || !groupId}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              Add Ledger
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Main Page ─── */
function SmartLedgerContent() {
  const {
    groups,
    summary,
    editableLedgers,
    isLoading,
    isSaving,
    error,
    saveResult,
    fetchGroups,
    fetchSuggestions,
    fetchClientLedgers,
    clientLedgers,
    addCustomLedger,
    removeLedger,
    updateLedgerName,
    updateLedgerGroup,
    bulkSaveLedgers,
    reset,
  } = useSmartLedgerStore();

  const { activeClient } = useClientStore();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Onboarding mode: came from "Create Client" flow
  const isOnboarding = searchParams.get("onboarding") === "1";
  const queryIndustry = searchParams.get("industry_type") || "";

  const [step, setStep] = useState(1);
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [search, setSearch] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [editIndex, setEditIndex] = useState<number | null>(null);

  // Fetch groups on mount
  useEffect(() => {
    fetchGroups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // If opened via onboarding redirect with an industry_type, auto-load suggestions
  useEffect(() => {
    if (isOnboarding && queryIndustry && editableLedgers.length === 0 && !isLoading) {
      setSelectedIndustry(queryIndustry);
      fetchSuggestions(queryIndustry).then(() => setStep(2));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOnboarding, queryIndustry]);

  // When active client has an industry_type, pre-select it (non-onboarding)
  useEffect(() => {
    if (!isOnboarding && activeClient?.industry_type && !selectedIndustry) {
      setSelectedIndustry(activeClient.industry_type);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeClient?.industry_type]);

  // Group the editable ledgers by their group_name
  const groupedLedgers = useMemo(() => {
    const map: Record<string, { ledgers: (LedgerSuggestion & { _idx: number })[]; count: number }> =
      {};
    editableLedgers.forEach((l, idx) => {
      const key = l.group_name || l.group || "Other";
      if (!map[key]) map[key] = { ledgers: [], count: 0 };
      // Apply search filter
      if (
        !search ||
        l.name.toLowerCase().includes(search.toLowerCase()) ||
        l.sub_category.toLowerCase().includes(search.toLowerCase()) ||
        key.toLowerCase().includes(search.toLowerCase())
      ) {
        map[key].ledgers.push({ ...l, _idx: idx });
      }
      map[key].count++;
    });
    return map;
  }, [editableLedgers, search]);

  /* ─── Step 1: Select Industry ─── */
  const handleIndustrySelect = async (industry: string) => {
    setSelectedIndustry(industry);
    await fetchSuggestions(industry);
    setStep(2);
  };

  /* ─── Step 3: Save ─── */
  const handleSave = async () => {
    setStep(3);
    await bulkSaveLedgers();
  };

  /* ─── Reset to Step 1 ─── */
  const handleReset = () => {
    reset();
    setStep(1);
    setSelectedIndustry("");
    setSearch("");
  };

  return (
    <div className="space-y-6">
      {/* Onboarding header banner */}
      {isOnboarding && (
        <div className="rounded-xl border border-green-200 bg-green-50 px-5 py-4 flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-green-800">
              Client <strong>{activeClient?.name}</strong> created successfully!
            </p>
            <p className="text-xs text-green-700 mt-0.5">
              Review and approve the suggested ledger accounts below, then go to Dashboard.
            </p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Smart Ledger</h1>
            <p className="text-sm text-gray-500">
              Auto-suggest & seed ledgers based on client industry.
            </p>
          </div>
        </div>
        <StepIndicator step={step} />
      </div>

      {/* Active Client Info */}
      {activeClient && (
        <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm">
          <Building2 className="h-4 w-4 text-gray-400" />
          <span className="font-medium text-gray-700">{activeClient.name}</span>
          {activeClient.gstin && (
            <span className="text-gray-400">· {activeClient.gstin}</span>
          )}
          {activeClient.industry_type && (
            <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 uppercase">
              {activeClient.industry_type}
            </span>
          )}
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* ═══════ STEP 1 ─ Select Industry ═══════ */}
      {step === 1 && (
        <div className="space-y-6">
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">
                Select Client Industry Type
              </h2>
            </div>
            <p className="mb-6 text-sm text-gray-500">
              Choose the industry to auto-suggest the right set of accounting ledgers — GST heads,
              bank accounts, expenses, income, and more.
            </p>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {INDUSTRY_CARDS.map((card) => {
                const Icon = card.icon;
                const isSelected = selectedIndustry === card.key;
                return (
                  <button
                    key={card.key}
                    onClick={() => handleIndustrySelect(card.key)}
                    disabled={isLoading}
                    className={cn(
                      "flex flex-col items-start gap-3 rounded-xl border-2 p-5 text-left transition-all",
                      card.bg,
                      isSelected && "ring-2 ring-blue-500 ring-offset-2"
                    )}
                  >
                    <div className={cn("rounded-lg bg-white p-2 shadow-sm", card.color)}>
                      <Icon className="h-6 w-6" />
                    </div>
                    <div>
                      <p className={cn("font-semibold", card.color)}>{card.label}</p>
                      <p className="text-xs text-gray-500 mt-1">{card.description}</p>
                    </div>
                  </button>
                );
              })}
            </div>

            {isLoading && (
              <div className="mt-6 flex items-center justify-center gap-2 text-blue-600">
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span className="text-sm">Generating suggestions…</span>
              </div>
            )}
          </div>

          {/* Existing ledgers quick view */}
          <ExistingLedgersCard
            activeClientId={activeClient?.id}
            fetchClientLedgers={fetchClientLedgers}
            clientLedgers={clientLedgers}
          />
        </div>
      )}

      {/* ═══════ STEP 2 ─ Review & Edit ═══════ */}
      {step === 2 && (
        <div className="space-y-4">
          {/* Summary banner */}
          {summary && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <SummaryCard
                label="Total Ledgers"
                value={editableLedgers.length}
                accent="blue"
              />
              <SummaryCard
                label="Industry Specific"
                value={summary.industry_specific_count}
                accent="purple"
              />
              <SummaryCard
                label="Groups"
                value={Object.keys(summary.by_group).length}
                accent="emerald"
              />
              <SummaryCard
                label="Custom Added"
                value={editableLedgers.filter((l) => l.is_custom).length}
                accent="orange"
              />
            </div>
          )}

          {/* Toolbar */}
          <div className="flex items-center justify-between gap-4">
            <button
              onClick={() => setStep(1)}
              className="flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </button>

            <div className="flex items-center gap-2 flex-1 max-w-md">
              <div className="flex flex-1 items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2">
                <Search className="h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Filter ledgers…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="flex-1 bg-transparent text-sm outline-none placeholder-gray-400"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                <Plus className="h-4 w-4" />
                Add Custom
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving || editableLedgers.length === 0}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                <Save className="h-4 w-4" />
                Save All ({editableLedgers.length})
              </button>
            </div>
          </div>

          {/* Grouped ledger lists */}
          <div className="space-y-4">
            {Object.keys(groupedLedgers).length === 0 ? (
              <div className="rounded-xl border border-gray-200 bg-white px-6 py-12 text-center text-gray-400">
                No ledgers match your filter.
              </div>
            ) : (
              Object.entries(groupedLedgers).map(([groupName, { ledgers, count }]) => (
                <div
                  key={groupName}
                  className="rounded-xl border border-gray-200 bg-white shadow-sm"
                >
                  {/* Group header */}
                  <div className="flex items-center justify-between border-b border-gray-100 px-5 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-800">{groupName}</span>
                      <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
                        {ledgers.length}
                        {search && ledgers.length !== count && ` / ${count}`}
                      </span>
                    </div>
                  </div>

                  {/* Ledger rows */}
                  <div className="divide-y divide-gray-50">
                    {ledgers.map((ledger) => (
                      <div
                        key={ledger._idx}
                        className="flex items-center gap-3 px-5 py-2.5 hover:bg-gray-50 transition-colors group"
                      >
                        {/* Name (editable on click) */}
                        <div className="flex-1 min-w-0">
                          {editIndex === ledger._idx ? (
                            <input
                              autoFocus
                              value={ledger.name}
                              onChange={(e) =>
                                updateLedgerName(ledger._idx, e.target.value)
                              }
                              onBlur={() => setEditIndex(null)}
                              onKeyDown={(e) => e.key === "Enter" && setEditIndex(null)}
                              className="w-full rounded border border-blue-300 px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-blue-500"
                            />
                          ) : (
                            <button
                              onClick={() => setEditIndex(ledger._idx)}
                              className="text-sm text-gray-800 truncate text-left w-full hover:text-blue-700"
                              title="Click to rename"
                            >
                              {ledger.name}
                            </button>
                          )}
                        </div>

                        {/* Sub-category badge */}
                        <span className="shrink-0 rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                          {ledger.sub_category}
                        </span>

                        {/* Custom badge */}
                        {ledger.is_custom && (
                          <span className="shrink-0 rounded bg-orange-50 px-2 py-0.5 text-xs font-medium text-orange-600">
                            Custom
                          </span>
                        )}

                        {/* Group selector (for custom ledgers) */}
                        {ledger.is_custom && groups.length > 0 && (
                          <select
                            value={ledger.group_id}
                            onChange={(e) => {
                              const g = groups.find((gr) => gr.id === e.target.value);
                              if (g) updateLedgerGroup(ledger._idx, g.id, g.name);
                            }}
                            className="shrink-0 rounded border border-gray-200 py-0.5 px-1.5 text-xs outline-none"
                          >
                            {groups.map((g) => (
                              <option key={g.id} value={g.id}>
                                {g.name}
                              </option>
                            ))}
                          </select>
                        )}

                        {/* Remove */}
                        <button
                          onClick={() => removeLedger(ledger._idx)}
                          className="shrink-0 rounded p-1 text-gray-300 hover:bg-red-50 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Remove"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Add Ledger Modal */}
          <AddLedgerModal
            open={showAddModal}
            groups={groups}
            onAdd={addCustomLedger}
            onClose={() => setShowAddModal(false)}
          />
        </div>
      )}

      {/* ═══════ STEP 3 ─ Save & Confirm ═══════ */}
      {step === 3 && (
        <div className="flex flex-col items-center justify-center py-12 space-y-6">
          {isSaving ? (
            <>
              <RefreshCw className="h-10 w-10 animate-spin text-blue-500" />
              <p className="text-lg font-medium text-gray-700">Saving ledgers…</p>
              <p className="text-sm text-gray-400">
                Creating and updating {editableLedgers.length} ledger accounts for{" "}
                <strong>{activeClient?.name}</strong>
              </p>
            </>
          ) : saveResult ? (
            <>
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <CheckCircle2 className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Ledgers Saved Successfully</h2>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="rounded-lg border border-gray-200 bg-white px-6 py-4">
                  <p className="text-2xl font-bold text-blue-600">{saveResult.created}</p>
                  <p className="text-xs text-gray-500">Created</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-white px-6 py-4">
                  <p className="text-2xl font-bold text-amber-600">{saveResult.updated}</p>
                  <p className="text-xs text-gray-500">Updated</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-white px-6 py-4">
                  <p className="text-2xl font-bold text-green-600">
                    {saveResult.total_client_ledgers}
                  </p>
                  <p className="text-xs text-gray-500">Total</p>
                </div>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleReset}
                  className="flex items-center gap-2 rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Start Over
                </button>
                {isOnboarding ? (
                  <button
                    onClick={() => router.push("/dashboard")}
                    className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    Go to Dashboard
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      fetchClientLedgers();
                      setStep(1);
                    }}
                    className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    <BookOpen className="h-4 w-4" />
                    View All Ledgers
                  </button>
                )}
              </div>
            </>
          ) : error ? (
            <>
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                <AlertCircle className="h-8 w-8 text-red-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Save Failed</h2>
              <p className="text-sm text-red-600">{error}</p>
              <button
                onClick={() => setStep(2)}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Go Back & Retry
              </button>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}

/* ─── Summary stat card ─── */
function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: "blue" | "purple" | "emerald" | "orange";
}) {
  const colors = {
    blue: "bg-blue-50 text-blue-700",
    purple: "bg-purple-50 text-purple-700",
    emerald: "bg-emerald-50 text-emerald-700",
    orange: "bg-orange-50 text-orange-700",
  };
  return (
    <div className="rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <p className={cn("text-2xl font-bold", colors[accent].split(" ")[1])}>{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}

/* ─── Existing Ledgers quick-view card ─── */
function ExistingLedgersCard({
  activeClientId,
  fetchClientLedgers,
  clientLedgers,
}: {
  activeClientId: string | undefined;
  fetchClientLedgers: (params?: Record<string, string>) => Promise<void>;
  clientLedgers: { id: string; name: string; group_name: string; is_custom: boolean }[];
}) {
  const [loaded, setLoaded] = useState(false);

  const handleLoad = async () => {
    if (!activeClientId) return;
    await fetchClientLedgers();
    setLoaded(true);
  };

  if (!activeClientId) return null;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">
          Existing Ledgers for this Client
        </h3>
        {!loaded && (
          <button
            onClick={handleLoad}
            className="text-xs font-medium text-blue-600 hover:underline"
          >
            Load
          </button>
        )}
      </div>
      {loaded ? (
        clientLedgers.length === 0 ? (
          <p className="text-sm text-gray-400">
            No ledgers yet. Select an industry above to get started.
          </p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {clientLedgers.slice(0, 30).map((l) => (
              <span
                key={l.id}
                className={cn(
                  "rounded px-2 py-0.5 text-xs",
                  l.is_custom
                    ? "bg-orange-50 text-orange-600"
                    : "bg-gray-100 text-gray-600"
                )}
              >
                {l.name}
              </span>
            ))}
            {clientLedgers.length > 30 && (
              <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-400">
                +{clientLedgers.length - 30} more
              </span>
            )}
          </div>
        )
      ) : (
        <p className="text-sm text-gray-400">Click "Load" to see existing ledgers.</p>
      )}
    </div>
  );
}

export default function SmartLedgerPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center text-gray-400 text-sm">
          Loading Smart Ledger…
        </div>
      }
    >
      <SmartLedgerContent />
    </Suspense>
  );
}
