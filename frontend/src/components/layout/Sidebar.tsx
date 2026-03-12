"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Upload,
  Database,
  Receipt,
  FileSearch,
  FolderOpen,
  BarChart3,
  FileText,
  BotMessageSquare,
  Settings,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * SIZH CA - Sidebar Navigation
 * Persistent sidebar with all main navigation links.
 */

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Clients", href: "/clients", icon: Users },
  { label: "Bulk Upload", href: "/bulk-upload", icon: Upload },
  { label: "Master", href: "/master", icon: Database },
  { label: "Transaction", href: "/transaction", icon: Receipt },
  { label: "GST Reco", href: "/gst-reco", icon: FileSearch },
  { label: "Document", href: "/document", icon: FolderOpen },
  { label: "Analysis", href: "/analysis", icon: BarChart3 },
  { label: "Reports", href: "/reports", icon: FileText },
  { label: "CA GPT", href: "/ca-gpt", icon: BotMessageSquare },
  { label: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-[72px] flex-col items-center border-r border-gray-200 bg-white py-4 shadow-sm transition-all hover:w-[220px] group">
      {/* Logo */}
      <div className="mb-6 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-lg">
        S
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col gap-1 w-full px-2 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname?.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                "hover:bg-blue-50 hover:text-blue-700",
                isActive
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600"
              )}
              title={item.label}
            >
              <Icon className="h-5 w-5 shrink-0" />
              <span className="hidden group-hover:inline-block whitespace-nowrap">
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom - Chat/Support icon */}
      <div className="mt-auto px-2 w-full">
        <button className="flex w-full items-center justify-center rounded-lg bg-blue-600 p-2.5 text-white hover:bg-blue-700 transition-colors">
          <BotMessageSquare className="h-5 w-5" />
        </button>
      </div>
    </aside>
  );
}
