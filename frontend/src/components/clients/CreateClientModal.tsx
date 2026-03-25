"use client";

import { useState } from "react";
import { useClientStore } from "@/store/client-store";
import { useRouter } from "next/navigation";
import { X, Building2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const GST_TYPES = [
  { value: "regular", label: "Regular" },
  { value: "composition", label: "Composition" },
  { value: "unregistered", label: "Unregistered" },
  { value: "isd", label: "Input Service Distributor (ISD)" },
];

const INDUSTRY_TYPES = [
  { value: "trading", label: "Trading" },
  { value: "service", label: "Service" },
  { value: "ecommerce", label: "E-Commerce" },
  { value: "manufacturing", label: "Manufacturing" },
];

const STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
  "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
  "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
  "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
  "Uttarakhand", "West Bengal",
];

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated?: (id: string) => void;
}

export default function CreateClientModal({ open, onClose, onCreated }: Props) {
  const { createClient, switchClient, fetchClients } = useClientStore();
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    trade_name: "",
    pan: "",
    gstin: "",
    gst_type: "regular",
    industry_type: "service",
    email: "",
    phone: "",
    address: "",
    state: "",
    pincode: "",
    financial_year_start: "04-01",
    tally_company_name: "",
  });

  if (!open) return null;

  const set = (k: keyof typeof form, v: string) =>
    setForm((prev) => ({ ...prev, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setError("Client name is required.");
      return;
    }
    setError("");
    setSaving(true);
    try {
      const created = await createClient(form);
      await fetchClients();
      // Auto-switch to the newly created client
      await switchClient(created.id);
      onCreated?.(created.id);
      onClose();
      // ► Redirect to Smart Ledger onboarding (not the dashboard)
      router.push(`/smart-ledger?onboarding=1&industry_type=${form.industry_type}`);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to create client. Please try again.";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-2xl rounded-xl bg-white shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">New Client Profile</h2>
          </div>
          <button onClick={onClose} className="rounded p-1 hover:bg-gray-100">
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="overflow-y-auto flex-1">
          <div className="px-6 py-5 space-y-5">
            {/* Error */}
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Row 1: Name + Trade name */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  Client Name <span className="text-red-500">*</span>
                </label>
                <input
                  value={form.name}
                  onChange={(e) => set("name", e.target.value)}
                  placeholder="e.g. Raj Hardware Pvt Ltd"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  Trade Name
                </label>
                <input
                  value={form.trade_name}
                  onChange={(e) => set("trade_name", e.target.value)}
                  placeholder="Trade / Brand name"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Row 2: PAN + GSTIN */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  PAN
                </label>
                <input
                  value={form.pan}
                  onChange={(e) => set("pan", e.target.value.toUpperCase())}
                  placeholder="ABCDE1234F"
                  maxLength={10}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono uppercase outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  GSTIN
                </label>
                <input
                  value={form.gstin}
                  onChange={(e) => set("gstin", e.target.value.toUpperCase())}
                  placeholder="27ABCDE1234F1Z5"
                  maxLength={15}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono uppercase outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Row 3: GST Type + Industry Type */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  GST Type
                </label>
                <select
                  value={form.gst_type}
                  onChange={(e) => set("gst_type", e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  {GST_TYPES.map((g) => (
                    <option key={g.value} value={g.value}>{g.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  Industry Type
                </label>
                <select
                  value={form.industry_type}
                  onChange={(e) => set("industry_type", e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Select…</option>
                  {INDUSTRY_TYPES.map((g) => (
                    <option key={g.value} value={g.value}>{g.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Row 4: Email + Phone */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  Email
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => set("email", e.target.value)}
                  placeholder="client@example.com"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  Phone
                </label>
                <input
                  type="tel"
                  value={form.phone}
                  onChange={(e) => set("phone", e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Row 5: Address */}
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                Address
              </label>
              <input
                value={form.address}
                onChange={(e) => set("address", e.target.value)}
                placeholder="Street address"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {/* Row 6: State + Pincode */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  State
                </label>
                <select
                  value={form.state}
                  onChange={(e) => set("state", e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Select state…</option>
                  {STATES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  Pincode
                </label>
                <input
                  value={form.pincode}
                  onChange={(e) => set("pincode", e.target.value)}
                  placeholder="400001"
                  maxLength={6}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Row 7: Tally Company + FY Start */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  Tally Company Name
                </label>
                <input
                  value={form.tally_company_name}
                  onChange={(e) => set("tally_company_name", e.target.value)}
                  placeholder="As in Tally"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
                  Financial Year Start
                </label>
                <select
                  value={form.financial_year_start}
                  onChange={(e) => set("financial_year_start", e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="04-01">April 1 (India standard)</option>
                  <option value="01-01">January 1</option>
                </select>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 border-t border-gray-200 px-6 py-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className={cn(
                "flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60",
              )}
            >
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating…
                </>
              ) : (
                "Create Client"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
