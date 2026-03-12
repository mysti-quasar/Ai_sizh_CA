"use client";

import AppLayout from "@/components/layout/AppLayout";

/**
 * Layout for all dashboard routes.
 * Wraps pages with the Sidebar + Topbar shell.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppLayout>{children}</AppLayout>;
}
