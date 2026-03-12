"use client";

import { FileSearch } from "lucide-react";

/**
 * SIZH CA - GST Reco Page
 */
export default function GstRecoPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
          <FileSearch className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">GST Reco</h1>
          <p className="text-sm text-gray-500">GST reconciliation — match GSTR-2A/2B with your purchase data.</p>
        </div>
      </div>

      <div className="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center">
        <FileSearch className="mx-auto h-12 w-12 text-gray-300" />
        <h3 className="mt-4 text-lg font-medium text-gray-600">GST Reco — Coming Soon</h3>
        <p className="mt-2 text-sm text-gray-400">This module is under development. Stay tuned for updates.</p>
      </div>
    </div>
  );
}
