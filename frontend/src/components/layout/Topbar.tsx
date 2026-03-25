"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth-store";
import { useClientStore } from "@/store/client-store";
import TallyStatusIndicator from "@/components/layout/TallyStatusIndicator";
import CreateClientModal from "@/components/clients/CreateClientModal";
import {
  ChevronDown,
  Bell,
  Plus,
  Search,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * SIZH CA - Top Navigation Bar
 * Contains client profile selector, search, notifications, and user menu.
 */

export default function Topbar() {
  const { user, logout } = useAuthStore();
  const { clients, activeClient, fetchClients, fetchActiveClient, switchClient } = useClientStore();
  const [showCreateClient, setShowCreateClient] = useState(false);
  const [clientSearch, setClientSearch] = useState("");

  useEffect(() => {
    fetchClients().catch(() => {});
    fetchActiveClient().catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleClientSwitch = async (clientId: string) => {
    try {
      await switchClient(clientId);
    } catch (error) {
      console.error("Failed to switch client:", error);
    }
  };

  const filteredClients = clients.filter((client) => {
    const q = clientSearch.trim().toLowerCase();
    if (!q) return true;
    return (
      client.name.toLowerCase().includes(q)
      || (client.trade_name || "").toLowerCase().includes(q)
      || (client.gstin || "").toLowerCase().includes(q)
      || (client.phone || "").toLowerCase().includes(q)
    );
  });

  return (
    <>
    <header className="fixed top-0 left-[72px] right-0 z-30 flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6 shadow-sm">
      {/* Left: Page title area */}
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-gray-800">Dashboard</h1>
      </div>

      {/* Center: Search */}
      <div className="hidden md:flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 w-80">
        <Search className="h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Type here to search..."
          className="flex-1 bg-transparent text-sm outline-none placeholder-gray-400"
        />
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3">
        {/* Tally connection status */}
        <TallyStatusIndicator />

        {/* Add new button → opens Create Client modal */}
        <button
          onClick={() => setShowCreateClient(true)}
          className="flex items-center justify-center h-8 w-8 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          title="New Client"
        >
          <Plus className="h-4 w-4" />
        </button>

        {/* Notifications */}
        <button className="relative flex items-center justify-center h-8 w-8 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white">
            3
          </span>
        </button>

        {/* Client Profile Selector */}
        <div className="relative group">
          <button className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
            <span className="max-w-[160px] truncate">
              {activeClient?.name || "Select Client"}
            </span>
            <ChevronDown className="h-3 w-3" />
          </button>

          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-1 hidden group-hover:block w-64 rounded-lg border border-gray-200 bg-white py-1 shadow-lg z-50">
            <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase">
              Client Profiles
            </div>
            <div className="px-3 pb-2">
              <div className="flex items-center gap-2 rounded-md border border-gray-200 px-2 py-1.5">
                <Search className="h-3.5 w-3.5 text-gray-400" />
                <input
                  value={clientSearch}
                  onChange={(e) => setClientSearch(e.target.value)}
                  placeholder="Search client..."
                  className="w-full bg-transparent text-xs text-gray-700 outline-none placeholder:text-gray-400"
                />
              </div>
            </div>
            {clients.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500">
                No clients yet. Create one in Settings.
              </div>
            ) : filteredClients.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500">
                No client found.
              </div>
            ) : (
              filteredClients.map((client) => (
                <button
                  key={client.id}
                  onClick={() => handleClientSwitch(client.id)}
                  className={cn(
                    "flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-blue-50 transition-colors",
                    activeClient?.id === client.id
                      ? "bg-blue-50 text-blue-700 font-medium"
                      : "text-gray-700"
                  )}
                >
                  <div className="flex h-6 w-6 items-center justify-center rounded bg-blue-100 text-blue-700 text-xs font-bold">
                    {client.name.charAt(0).toUpperCase()}
                  </div>
                  <span className="truncate">{client.name}</span>
                  {client.gstin && (
                    <span className="ml-auto text-xs text-gray-400">{client.gstin}</span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* User avatar & menu */}
        <div className="relative group">
          <button className="flex items-center gap-2 rounded-lg px-2 py-1 hover:bg-gray-50 transition-colors">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-white text-sm font-medium">
              {user?.first_name?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <span className="hidden lg:block text-sm font-medium text-gray-700">
              {user?.first_name || "User"}
            </span>
            <ChevronDown className="h-3 w-3 text-gray-400" />
          </button>

          {/* User Dropdown */}
          <div className="absolute right-0 top-full mt-1 hidden group-hover:block w-48 rounded-lg border border-gray-200 bg-white py-1 shadow-lg z-50">
            <div className="px-3 py-2 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-800">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
            <button
              onClick={logout}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>

    {/* Create Client Modal – rendered outside header for proper stacking */}
    <CreateClientModal
      open={showCreateClient}
      onClose={() => setShowCreateClient(false)}
    />
    </>
  );
}
