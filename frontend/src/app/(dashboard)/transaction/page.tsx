"use client";

import { useEffect } from "react";
import { useUploadStore, type UploadJob } from "@/store/upload-store";
import {
  Receipt,
  RefreshCw,
  FileSpreadsheet,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Send,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  uploaded: { icon: <Clock className="h-3.5 w-3.5" />, color: "bg-gray-100 text-gray-600", label: "Uploaded" },
  parsing: { icon: <Loader2 className="h-3.5 w-3.5 animate-spin" />, color: "bg-blue-100 text-blue-700", label: "Parsing" },
  parsed: { icon: <FileSpreadsheet className="h-3.5 w-3.5" />, color: "bg-blue-100 text-blue-700", label: "Parsed" },
  mapping: { icon: <Loader2 className="h-3.5 w-3.5 animate-spin" />, color: "bg-amber-100 text-amber-700", label: "Mapping" },
  mapped: { icon: <FileSpreadsheet className="h-3.5 w-3.5" />, color: "bg-amber-100 text-amber-700", label: "Mapped" },
  ai_processing: { icon: <Loader2 className="h-3.5 w-3.5 animate-spin" />, color: "bg-purple-100 text-purple-700", label: "AI Processing" },
  ready: { icon: <CheckCircle2 className="h-3.5 w-3.5" />, color: "bg-green-100 text-green-700", label: "Ready" },
  approved: { icon: <CheckCircle2 className="h-3.5 w-3.5" />, color: "bg-green-100 text-green-700", label: "Approved" },
  sent_to_tally: { icon: <Send className="h-3.5 w-3.5" />, color: "bg-green-100 text-green-700", label: "Sent to Tally" },
  failed: { icon: <AlertTriangle className="h-3.5 w-3.5" />, color: "bg-red-100 text-red-700", label: "Failed" },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.uploaded;
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium", cfg.color)}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

export default function TransactionPage() {
  const { jobs, isLoading, fetchJobs } = useUploadStore();

  useEffect(() => {
    fetchJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
            <Receipt className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
            <p className="text-sm text-gray-500">Upload jobs and transaction history.</p>
          </div>
        </div>
        <button
          onClick={() => fetchJobs()}
          disabled={isLoading}
          className="flex items-center gap-2 rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          Refresh
        </button>
      </div>

      {/* Loading */}
      {isLoading && jobs.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && jobs.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center">
          <Receipt className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-600">No Transactions Yet</h3>
          <p className="mt-2 text-sm text-gray-400">
            Upload files from the Bulk Upload page to see transactions here.
          </p>
        </div>
      )}

      {/* Jobs table */}
      {jobs.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              <tr>
                <th className="px-4 py-3">File</th>
                <th className="px-4 py-3">Voucher Type</th>
                <th className="px-4 py-3">Bank</th>
                <th className="px-4 py-3">Rows</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <FileSpreadsheet className="h-4 w-4 text-gray-400" />
                      <span className="font-medium text-gray-800 max-w-[200px] truncate">
                        {job.original_filename || "—"}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 capitalize">
                      {job.voucher_type?.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{job.bank_account || "—"}</td>
                  <td className="px-4 py-3 tabular-nums text-gray-600">{job.row_count}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {job.created_at ? new Date(job.created_at).toLocaleString() : "—"}
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
