"use client";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

/**
 * SIZH CA - Main Application Layout
 * Wraps all authenticated pages with Sidebar + Topbar.
 */

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <Topbar />
      {/* Main content area - offset by sidebar width and topbar height */}
      <main className="ml-[72px] mt-14 p-6">
        {children}
      </main>
    </div>
  );
}
