"use client";

import { useEffect, useState } from "react";
import { useClientStore } from "@/store/client-store";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import {
  LayoutDashboard,
  Upload,
  Database,
  Receipt,
  Building2,
  BookOpen,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface DashboardStats {
  upload_jobs: number;
  transaction_rows: number;
  tally_vouchers: number;
  client_ledgers: number;
}

/**
 * SIZH CA - Dashboard Page
 * Shows live stats for the currently selected client.
 */
export default function DashboardPage() {
  const { activeClient, fetchActiveClient } = useClientStore();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(false);

  // Refresh active client on mount (in case persisted state is stale)
  useEffect(() => {
    fetchActiveClient();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch stats whenever active client changes
  useEffect(() => {
    if (!activeClient?.id) return;
    setLoading(true);
    Promise.all([
      api.get("/transactions/jobs/").catch(() => ({ data: { results: [] } })),
      api.get("/masters/client-ledgers/").catch(() => ({ data: { results: [] } })),
    ])
      .then(([jobsRes, ledgersRes]) => {
        const jobs = jobsRes.data.results || jobsRes.data || [];
        const ledgers = ledgersRes.data.results || ledgersRes.data || [];
        setStats({
          upload_jobs: jobs.length,
          transaction_rows: jobs.reduce((sum: number, j: { row_count?: number }) => sum + (j.row_count || 0), 0),
          tally_vouchers: 0,
          client_ledgers: ledgers.length,
        });
      })
      .finally(() => setLoading(false));
  }, [activeClient?.id]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
          <LayoutDashboard className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500">
            Overview of your accounting workspace with key metrics and insights.
          </p>
        </div>
      </div>

      {/* No client selected */}
      {!activeClient ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-amber-800">No Client Selected</h3>
              <p className="mt-1 text-sm text-amber-700">
                Use the <strong>Select Client</strong> dropdown in the top bar to choose a client,
                or click the <strong>+</strong> button to create a new one.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Active Client Card */}
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white text-lg font-bold">
                  {activeClient.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h2 className="text-base font-bold text-blue-900">{activeClient.name}</h2>
                  <div className="flex items-center gap-3 mt-0.5 text-xs text-blue-700">
                    {activeClient.gstin && <span>{activeClient.gstin}</span>}
                    {activeClient.industry_type && (
                      <span className="rounded bg-blue-200 px-1.5 py-0.5 font-medium uppercase">
                        {activeClient.industry_type}
                      </span>
                    )}
                    {activeClient.state && <span>{activeClient.state}</span>}
                  </div>
                </div>
              </div>
              <Building2 className="h-5 w-5 text-blue-400" />
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="rounded-xl border border-gray-200 bg-white p-5 animate-pulse">
                  <div className="h-4 w-20 rounded bg-gray-100 mb-2" />
                  <div className="h-7 w-12 rounded bg-gray-100" />
                </div>
              ))
            ) : (
              [
                { label: "Upload Jobs", value: stats?.upload_jobs ?? 0, icon: Upload, color: "blue" },
                { label: "Transactions", value: stats?.transaction_rows ?? 0, icon: Receipt, color: "green" },
                { label: "Tally Vouchers", value: stats?.tally_vouchers ?? 0, icon: Database, color: "purple" },
                { label: "Client Ledgers", value: stats?.client_ledgers ?? 0, icon: BookOpen, color: "orange" },
              ].map((stat) => {
                const Icon = stat.icon;
                const colors: Record<string, string> = {
                  blue: "bg-blue-50 text-blue-700",
                  green: "bg-emerald-50 text-emerald-700",
                  purple: "bg-purple-50 text-purple-700",
                  orange: "bg-orange-50 text-orange-700",
                };
                return (
                  <div key={stat.label} className="rounded-xl border border-gray-200 bg-white p-5">
                    <div className={cn("mb-3 inline-flex rounded-lg p-2", colors[stat.color])}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <p className="text-sm text-gray-500">{stat.label}</p>
                    <p className="mt-0.5 text-2xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                );
              })
            )}
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                title: "Bulk Upload",
                description: "Upload bank statements, invoices, or ledgers via AI parsing.",
                href: "/bulk-upload",
                icon: Upload,
                color: "blue",
              },
              {
                title: "Smart Ledger",
                description: "Review and manage ledger accounts for this client.",
                href: `/smart-ledger`,
                icon: BookOpen,
                color: "emerald",
              },
              {
                title: "Document Vault",
                description: "Organise and upload client documents in folders.",
                href: "/document",
                icon: Database,
                color: "purple",
              },
            ].map((action) => {
              const Icon = action.icon;
              const colors: Record<string, string> = {
                blue: "bg-blue-50 text-blue-700 hover:bg-blue-100",
                emerald: "bg-emerald-50 text-emerald-700 hover:bg-emerald-100",
                purple: "bg-purple-50 text-purple-700 hover:bg-purple-100",
              };
              return (
                <button
                  key={action.title}
                  onClick={() => router.push(action.href)}
                  className="flex items-start gap-4 rounded-xl border border-gray-200 bg-white p-5 text-left hover:border-blue-200 hover:shadow-sm transition-all group"
                >
                  <div className={cn("rounded-lg p-2.5 shrink-0", colors[action.color])}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{action.title}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">{action.description}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-gray-300 group-hover:text-gray-500 mt-1 transition-colors" />
                </button>
              );
            })}
          </div>

          {/* Setup nudge if no ledgers */}
          {stats?.client_ledgers === 0 && !loading && (
            <div className="rounded-xl border border-dashed border-blue-300 bg-blue-50 p-6 text-center">
              <BookOpen className="mx-auto h-10 w-10 text-blue-400 mb-3" />
              <h3 className="font-semibold text-blue-900">Set Up Ledger Accounts</h3>
              <p className="text-sm text-blue-700 mt-1 mb-4">
                This client has no ledger accounts yet. Set them up using Smart Ledger.
              </p>
              <button
                onClick={() => router.push("/smart-ledger")}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <BookOpen className="h-4 w-4" />
                Set Up Ledgers
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
