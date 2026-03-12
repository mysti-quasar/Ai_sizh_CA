"use client";

import { BarChart3 } from "lucide-react";

/**
 * SIZH CA - Analysis Page
 */
export default function AnalysisPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
          <BarChart3 className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analysis</h1>
          <p className="text-sm text-gray-500">AI-powered analytics and insights across your accounting data.</p>
        </div>
      </div>

      <div className="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center">
        <BarChart3 className="mx-auto h-12 w-12 text-gray-300" />
        <h3 className="mt-4 text-lg font-medium text-gray-600">Analysis — Coming Soon</h3>
        <p className="mt-2 text-sm text-gray-400">This module is under development. Stay tuned for updates.</p>
      </div>
    </div>
  );
}
