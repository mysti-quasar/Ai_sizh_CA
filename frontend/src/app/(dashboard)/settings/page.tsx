"use client";

import { useEffect, useState } from "react";
import { useMastersStore, type Rule, type TallyLedger } from "@/store/masters-store";
import {
  Settings,
  Plus,
  Pencil,
  Trash2,
  Save,
  X,
  ChevronDown,
  BookOpen,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

const RULE_TYPES = [
  { value: "payment", label: "Payment" },
  { value: "receipt", label: "Receipt" },
  { value: "contra", label: "Contra" },
  { value: "journal", label: "Journal" },
  { value: "sales", label: "Sales" },
  { value: "purchase", label: "Purchase" },
];

const emptyRule: Partial<Rule> = {
  description: "",
  rule_type: "payment",
  from_field: "",
  to_field: "",
  target_ledger: null,
  priority: 0,
  is_active: true,
};

export default function SettingsPage() {
  const { rules, ledgers, isLoading, fetchRules, fetchLedgers, createRule, updateRule, deleteRule } =
    useMastersStore();

  const [editing, setEditing] = useState<Partial<Rule> | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchRules();
    fetchLedgers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSave = async () => {
    if (!editing) return;
    try {
      if (editId) {
        await updateRule(editId, editing);
      } else {
        await createRule(editing);
      }
      setShowForm(false);
      setEditing(null);
      setEditId(null);
    } catch (e) {
      console.error("Failed to save rule:", e);
    }
  };

  const handleEdit = (rule: Rule) => {
    setEditing({ ...rule });
    setEditId(rule.id);
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this rule?")) return;
    await deleteRule(id);
  };

  const handleNew = () => {
    setEditing({ ...emptyRule });
    setEditId(null);
    setShowForm(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
            <Settings className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Settings & Rules</h1>
            <p className="text-sm text-gray-500">
              Configure auto-ledger matching rules for bulk upload.
            </p>
          </div>
        </div>
        <button
          onClick={handleNew}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Rule
        </button>
      </div>

      {/* Rule form */}
      {showForm && editing && (
        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-6 space-y-4">
          <h3 className="text-sm font-semibold text-gray-700">
            {editId ? "Edit Rule" : "Create New Rule"}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Description */}
            <div className="lg:col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
              <input
                type="text"
                value={editing.description || ""}
                onChange={(e) => setEditing({ ...editing, description: e.target.value })}
                placeholder="e.g. UPI payments to XYZ → Expense A/c"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
            {/* Rule Type */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Rule Type</label>
              <select
                value={editing.rule_type || "payment"}
                onChange={(e) => setEditing({ ...editing, rule_type: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
              >
                {RULE_TYPES.map((rt) => (
                  <option key={rt.value} value={rt.value}>
                    {rt.label}
                  </option>
                ))}
              </select>
            </div>
            {/* From field (keyword) */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                From (keyword in description)
              </label>
              <input
                type="text"
                value={editing.from_field || ""}
                onChange={(e) => setEditing({ ...editing, from_field: e.target.value })}
                placeholder="e.g. NEFT, UPI, Salary"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
            {/* To field */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                To (optional keyword)
              </label>
              <input
                type="text"
                value={editing.to_field || ""}
                onChange={(e) => setEditing({ ...editing, to_field: e.target.value })}
                placeholder="e.g. additional match text"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
            {/* Target Ledger */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Target Ledger</label>
              <select
                value={editing.target_ledger || ""}
                onChange={(e) =>
                  setEditing({ ...editing, target_ledger: e.target.value || null })
                }
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
              >
                <option value="">— Select ledger —</option>
                {ledgers.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name} {l.group ? `(${l.group})` : ""}
                  </option>
                ))}
              </select>
            </div>
            {/* Priority */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Priority</label>
              <input
                type="number"
                value={editing.priority ?? 0}
                onChange={(e) =>
                  setEditing({ ...editing, priority: parseInt(e.target.value) || 0 })
                }
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
            {/* Active */}
            <div className="flex items-end gap-2 pb-1">
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={editing.is_active ?? true}
                  onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600"
                />
                Active
              </label>
            </div>
          </div>
          <div className="flex items-center gap-2 pt-2">
            <button
              onClick={handleSave}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              <Save className="h-4 w-4" />
              {editId ? "Update" : "Create"}
            </button>
            <button
              onClick={() => {
                setShowForm(false);
                setEditing(null);
                setEditId(null);
              }}
              className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <X className="h-4 w-4" />
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Rules list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
        </div>
      ) : rules.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center">
          <BookOpen className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-600">No Rules Yet</h3>
          <p className="mt-2 text-sm text-gray-400">
            Create rules to auto-assign ledgers during bulk upload.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              <tr>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">From</th>
                <th className="px-4 py-3">To</th>
                <th className="px-4 py-3">Target Ledger</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Active</th>
                <th className="px-4 py-3 w-24">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rules.map((rule) => (
                <tr key={rule.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-800">{rule.description}</td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-purple-50 px-2 py-0.5 text-xs font-medium text-purple-700 capitalize">
                      {rule.rule_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{rule.from_field}</td>
                  <td className="px-4 py-3 text-gray-600">{rule.to_field || "—"}</td>
                  <td className="px-4 py-3 text-gray-600">{rule.target_ledger_name || "—"}</td>
                  <td className="px-4 py-3 text-gray-600 tabular-nums">{rule.priority}</td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-block h-2 w-2 rounded-full",
                        rule.is_active ? "bg-green-500" : "bg-gray-300"
                      )}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleEdit(rule)}
                        className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-blue-600 transition-colors"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(rule.id)}
                        className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
