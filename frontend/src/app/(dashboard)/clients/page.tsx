"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useClientStore } from "@/store/client-store";
import type { ClientProfile } from "@/store/client-store";
import { Search, X, Users, Plus, Eye, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import CreateClientModal from "@/components/clients/CreateClientModal";

// ── helpers ──────────────────────────────────────────────────────────────────

/** Wrap query matches in <mark> tags, case-insensitive. */
function highlight(text: string, query: string): React.ReactNode {
  if (!query.trim() || !text) return <>{text || "—"}</>;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const testRe = new RegExp(escaped, "i"); // no `g` → safe to call .test() repeatedly
  return (
    <>
      {text.split(new RegExp(`(${escaped})`, "gi")).map((part, i) =>
        testRe.test(part) ? (
          <mark key={i} className="bg-yellow-200 text-yellow-900 rounded px-0.5">
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </>
  );
}

// ── component ─────────────────────────────────────────────────────────────────

export default function ClientsPage() {
  const { clients, activeClient, fetchClients, switchClient, isLoading } =
    useClientStore();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ClientProfile[]>([]);
  const [searching, setSearching] = useState(false);
  const [focusedRow, setFocusedRow] = useState<number>(-1);
  const [showCreate, setShowCreate] = useState(false);
  const [switchingId, setSwitchingId] = useState<string | null>(null);

  const searchRef = useRef<HTMLInputElement>(null);

  // ── initial data load ──────────────────────────────────────────────────────
  useEffect(() => {
    fetchClients().catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // When there is no active search, mirror the full store list
  useEffect(() => {
    if (!query.trim()) setResults(clients);
  }, [clients, query]);

  // ── debounced search (300 ms) ──────────────────────────────────────────────
  useEffect(() => {
    if (!query.trim()) {
      setResults(clients);
      setSearching(false);
      return;
    }

    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const { data } = await api.get(
          `/clients/search/?q=${encodeURIComponent(query.trim())}`
        );
        setResults(data.results ?? data);
      } catch {
        // Graceful fallback: filter locally
        const q = query.toLowerCase();
        setResults(
          clients.filter(
            (c) =>
              c.name?.toLowerCase().includes(q) ||
              c.trade_name?.toLowerCase().includes(q) ||
              c.gstin?.toLowerCase().includes(q) ||
              c.pan?.toLowerCase().includes(q) ||
              c.phone?.toLowerCase().includes(q)
          )
        );
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  // ── actions ────────────────────────────────────────────────────────────────
  const handleSelect = useCallback(
    async (clientId: string) => {
      setSwitchingId(clientId);
      try {
        await switchClient(clientId);
      } finally {
        setSwitchingId(null);
      }
    },
    [switchClient]
  );

  const clearSearch = () => {
    setQuery("");
    setFocusedRow(-1);
    searchRef.current?.focus();
  };

  // ── keyboard navigation ────────────────────────────────────────────────────
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedRow((r) => Math.min(r + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedRow((r) => Math.max(r - 1, 0));
    } else if (e.key === "Enter" && focusedRow >= 0) {
      handleSelect(results[focusedRow].id);
    } else if (e.key === "Escape") {
      clearSearch();
    }
  };

  // ── render ─────────────────────────────────────────────────────────────────
  const busy = isLoading || searching;

  return (
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div
      className="space-y-6 outline-none"
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Client Management
            </h1>
            <p className="text-sm text-gray-500">
              Search and manage all client profiles in your CA firm.
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Client
        </button>
      </div>

      {/* ── Search bar ── */}
      <div className="relative flex items-center rounded-xl border border-gray-200 bg-white shadow-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
        <Search className="absolute left-4 h-5 w-5 text-gray-400 shrink-0" />
        <input
          ref={searchRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setFocusedRow(-1);
          }}
          placeholder="Search by name, company, GST number, PAN, or phone…"
          className="w-full rounded-xl bg-transparent py-3 pl-12 pr-11 text-sm outline-none placeholder-gray-400"
          autoComplete="off"
          spellCheck={false}
        />
        {/* Spinner while searching */}
        {searching && (
          <div className="absolute right-10 flex items-center">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        )}
        {/* Clear button */}
        {query && (
          <button
            onClick={clearSearch}
            className="absolute right-3 flex h-6 w-6 items-center justify-center rounded-full bg-gray-200 text-gray-500 hover:bg-gray-300 transition-colors"
            title="Clear search"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* ── Results summary ── */}
      <p className="text-sm text-gray-500">
        {busy ? (
          "Searching…"
        ) : (
          <>
            <span className="font-medium text-gray-700">{results.length}</span>{" "}
            client{results.length !== 1 ? "s" : ""}
            {query && (
              <>
                {" "}
                matching{" "}
                <span className="font-medium text-gray-700">
                  &ldquo;{query}&rdquo;
                </span>
              </>
            )}
          </>
        )}
      </p>

      {/* ── Table ── */}
      <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Client Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Company Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                GST Number
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                PAN
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Phone
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {/* Loading skeleton */}
            {busy && results.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-14 text-center">
                  <div className="flex flex-col items-center gap-2 text-gray-400">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                    <span className="text-sm">Loading clients…</span>
                  </div>
                </td>
              </tr>
            ) : results.length === 0 ? (
              /* Empty state */
              <tr>
                <td colSpan={6} className="px-4 py-14 text-center">
                  <div className="flex flex-col items-center gap-2">
                    <Users className="h-8 w-8 text-gray-300" />
                    <p className="font-medium text-gray-500">No client found</p>
                    {query && (
                      <p className="text-sm text-gray-400">
                        No results for{" "}
                        <strong>&ldquo;{query}&rdquo;</strong>.{" "}
                        <button
                          onClick={clearSearch}
                          className="text-blue-600 hover:underline"
                        >
                          Clear search
                        </button>
                      </p>
                    )}
                  </div>
                </td>
              </tr>
            ) : (
              results.map((client, idx) => {
                const isActive = client.id === activeClient?.id;
                const isFocused = idx === focusedRow;
                const isSwitching = switchingId === client.id;

                return (
                  <tr
                    key={client.id}
                    className={cn(
                      "transition-colors cursor-default",
                      isFocused
                        ? "bg-blue-50"
                        : isActive
                        ? "bg-blue-50/40"
                        : "hover:bg-gray-50"
                    )}
                    onMouseEnter={() => setFocusedRow(idx)}
                    onMouseLeave={() => setFocusedRow(-1)}
                  >
                    {/* Client Name */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-xs font-bold">
                          {client.name?.charAt(0)?.toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-900">
                          {highlight(client.name ?? "", query)}
                        </span>
                        {isActive && (
                          <span className="flex items-center gap-1 text-xs font-medium text-blue-600">
                            <CheckCircle2 className="h-3 w-3" />
                            Active
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Company Name (trade_name) */}
                    <td className="px-4 py-3 text-gray-600">
                      {client.trade_name
                        ? highlight(client.trade_name, query)
                        : "—"}
                    </td>

                    {/* GSTIN */}
                    <td className="px-4 py-3 font-mono text-xs text-gray-600 tracking-wide">
                      {client.gstin ? highlight(client.gstin, query) : "—"}
                    </td>

                    {/* PAN */}
                    <td className="px-4 py-3 font-mono text-xs text-gray-600 tracking-wide">
                      {client.pan ? highlight(client.pan, query) : "—"}
                    </td>

                    {/* Phone */}
                    <td className="px-4 py-3 text-gray-600">
                      {client.phone ? highlight(client.phone, query) : "—"}
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleSelect(client.id)}
                          disabled={isActive || isSwitching}
                          className={cn(
                            "rounded-lg px-3 py-1.5 text-xs font-medium transition-colors min-w-[68px]",
                            isActive
                              ? "bg-green-100 text-green-700 cursor-default"
                              : "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
                          )}
                        >
                          {isSwitching ? (
                            <span className="flex items-center gap-1">
                              <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent inline-block" />
                              …
                            </span>
                          ) : isActive ? (
                            "Selected"
                          ) : (
                            "Select"
                          )}
                        </button>
                        <button
                          onClick={() => handleSelect(client.id)}
                          className="flex items-center gap-1 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
                          title="View client"
                        >
                          <Eye className="h-3 w-3" />
                          View
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Keyboard hint */}
      {results.length > 0 && (
        <p className="text-xs text-gray-400 text-center select-none">
          ↑↓ Navigate &nbsp;·&nbsp; Enter to select &nbsp;·&nbsp; Esc to clear
          search
        </p>
      )}

      <CreateClientModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={() => fetchClients()}
      />
    </div>
  );
}
