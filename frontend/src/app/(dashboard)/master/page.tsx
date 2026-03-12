"use client";

import { useEffect, useState, useMemo } from "react";
import { useMastersStore, type TallyLedger, type TallyItem, type ClientLedger } from "@/store/masters-store";
import { useTallyStore } from "@/store/tally-store";
import { useClientStore } from "@/store/client-store";
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import {
  Database,
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ArrowUpDown,
  Package,
  BookOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";

type Tab = "client_ledgers" | "ledgers" | "items";

/** ─── Ledger columns ─── */
const ledgerColumns: ColumnDef<TallyLedger>[] = [
  { accessorKey: "name", header: "Name", size: 200 },
  { accessorKey: "alias", header: "Alias", size: 120 },
  { accessorKey: "group", header: "Group", size: 150 },
  { accessorKey: "parent_group", header: "Parent Group", size: 150 },
  {
    accessorKey: "tax_category",
    header: "Tax",
    size: 80,
    cell: ({ getValue }) => (
      <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 uppercase">
        {(getValue() as string) || "—"}
      </span>
    ),
  },
  { accessorKey: "gstin", header: "GSTIN", size: 160 },
  { accessorKey: "state", header: "State", size: 100 },
  {
    accessorKey: "opening_balance",
    header: "Opening Bal.",
    size: 120,
    cell: ({ getValue }) => {
      const v = getValue() as number;
      return (
        <span className={cn("tabular-nums", v < 0 ? "text-red-600" : "text-gray-900")}>
          {v?.toLocaleString("en-IN", { minimumFractionDigits: 2 }) ?? "0.00"}
        </span>
      );
    },
  },
  {
    accessorKey: "is_active",
    header: "Active",
    size: 70,
    cell: ({ getValue }) => (
      <span
        className={cn(
          "inline-block h-2 w-2 rounded-full",
          getValue() ? "bg-green-500" : "bg-gray-300"
        )}
      />
    ),
  },
];

/** ─── Item columns ─── */
const itemColumns: ColumnDef<TallyItem>[] = [
  { accessorKey: "name", header: "Name", size: 200 },
  { accessorKey: "group", header: "Group", size: 150 },
  { accessorKey: "category", header: "Category", size: 120 },
  { accessorKey: "uom", header: "UOM", size: 80 },
  { accessorKey: "hsn_code", header: "HSN Code", size: 100 },
  {
    accessorKey: "gst_rate",
    header: "GST %",
    size: 80,
    cell: ({ getValue }) => <span className="tabular-nums">{getValue() as number}%</span>,
  },
  {
    accessorKey: "opening_stock",
    header: "Opening Qty",
    size: 110,
    cell: ({ getValue }) => (
      <span className="tabular-nums">{(getValue() as number)?.toLocaleString() ?? "0"}</span>
    ),
  },
  {
    accessorKey: "opening_value",
    header: "Opening Val.",
    size: 120,
    cell: ({ getValue }) => (
      <span className="tabular-nums">
        ₹{(getValue() as number)?.toLocaleString("en-IN", { minimumFractionDigits: 2 }) ?? "0.00"}
      </span>
    ),
  },
  {
    accessorKey: "is_active",
    header: "Active",
    size: 70,
    cell: ({ getValue }) => (
      <span
        className={cn(
          "inline-block h-2 w-2 rounded-full",
          getValue() ? "bg-green-500" : "bg-gray-300"
        )}
      />
    ),
  },
];

/** ─── Client Ledger columns ─── */
const clientLedgerColumns: ColumnDef<ClientLedger>[] = [
  { accessorKey: "name", header: "Ledger Name", size: 220 },
  { accessorKey: "group_name", header: "Group", size: 160 },
  { accessorKey: "group_code", header: "Code", size: 100 },
  { accessorKey: "sub_category", header: "Sub-Category", size: 140,
    cell: ({ getValue }) => (getValue() as string) || <span className="text-gray-400">—</span> },
  {
    accessorKey: "opening_balance",
    header: "Opening Bal.",
    size: 130,
    cell: ({ getValue }) => {
      const v = getValue() as number;
      return (
        <span className={cn("tabular-nums", v < 0 ? "text-red-600" : "text-gray-900")}>
          {v?.toLocaleString("en-IN", { minimumFractionDigits: 2 }) ?? "0.00"}
        </span>
      );
    },
  },
  {
    accessorKey: "is_custom",
    header: "Type",
    size: 80,
    cell: ({ getValue }) => (
      <span className={cn(
        "rounded-full px-2 py-0.5 text-xs font-medium",
        getValue() ? "bg-amber-100 text-amber-700" : "bg-blue-50 text-blue-700"
      )}>
        {getValue() ? "Custom" : "Template"}
      </span>
    ),
  },
  {
    accessorKey: "is_active",
    header: "Active",
    size: 70,
    cell: ({ getValue }) => (
      <span className={cn("inline-block h-2 w-2 rounded-full", getValue() ? "bg-green-500" : "bg-gray-300")} />
    ),
  },
];

/** ─── Reusable data table ─── */
function DataTable<T>({
  data,
  columns,
  globalFilter,
}: {
  data: T[];
  columns: ColumnDef<T, unknown>[];
  globalFilter: string;
}) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 25 } },
  });

  return (
    <div className="space-y-3">
      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((h) => (
                  <th
                    key={h.id}
                    className="whitespace-nowrap px-4 py-3 cursor-pointer select-none"
                    style={{ width: h.getSize() }}
                    onClick={h.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(h.column.columnDef.header, h.getContext())}
                      <ArrowUpDown className="h-3 w-3 text-gray-400" />
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center text-gray-400">
                  No data found.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50 transition-colors">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="whitespace-nowrap px-4 py-2.5 text-gray-700">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>
          Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}–
          {Math.min(
            (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
            table.getFilteredRowModel().rows.length
          )}{" "}
          of {table.getFilteredRowModel().rows.length}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
            className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"
          >
            <ChevronsLeft className="h-4 w-4" />
          </button>
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="px-2">
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </span>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
          <button
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
            className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"
          >
            <ChevronsRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

/** ─── Master Page ─── */
export default function MasterPage() {
  const { ledgers, items, ledgerCount, itemCount, clientLedgers, clientLedgerCount, isLoading, fetchLedgers, fetchItems, fetchClientLedgers } =
    useMastersStore();
  const { status, syncLedgers, syncItems } = useTallyStore();
  const { activeClient } = useClientStore();
  const [tab, setTab] = useState<Tab>("client_ledgers");
  const [search, setSearch] = useState("");
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchLedgers();
    fetchItems();
    fetchClientLedgers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeClient?.id]);

  const handleSync = async () => {
    if (!activeClient?.id) return;
    setSyncing(true);
    try {
      if (tab === "ledgers") {
        await syncLedgers(activeClient.id);
        await fetchLedgers();
      } else {
        await syncItems(activeClient.id);
        await fetchItems();
      }
    } finally {
      setSyncing(false);
    }
  };

  const tabs: { key: Tab; label: string; icon: React.ReactNode; count: number }[] = [
    { key: "client_ledgers", label: "My Ledgers", icon: <BookOpen className="h-4 w-4" />, count: clientLedgerCount },
    { key: "ledgers", label: "Tally Ledgers", icon: <BookOpen className="h-4 w-4" />, count: ledgerCount },
    { key: "items", label: "Items", icon: <Package className="h-4 w-4" />, count: itemCount },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
            <Database className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Master Data</h1>
            <p className="text-sm text-gray-500">
              Tally Ledgers, Stock Items, and mapping rules.
            </p>
          </div>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing || !status.connected}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={cn("h-4 w-4", syncing && "animate-spin")} />
          Sync from Tally
        </button>
      </div>

      {/* Tabs + Search */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={cn(
                "flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors",
                tab === t.key
                  ? "bg-white text-blue-700 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              )}
            >
              {t.icon}
              {t.label}
              <span
                className={cn(
                  "rounded-full px-2 py-0.5 text-xs",
                  tab === t.key ? "bg-blue-100 text-blue-700" : "bg-gray-200 text-gray-500"
                )}
              >
                {t.count}
              </span>
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 w-72">
          <Search className="h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, group, GSTIN…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 bg-transparent text-sm outline-none placeholder-gray-400"
          />
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
        </div>
      )}

      {/* Data Table */}
      {!isLoading && tab === "client_ledgers" && (
        <DataTable<ClientLedger>
          data={clientLedgers}
          columns={clientLedgerColumns as ColumnDef<ClientLedger, unknown>[]}
          globalFilter={search}
        />
      )}
      {!isLoading && tab === "ledgers" && (
        <DataTable<TallyLedger>
          data={ledgers}
          columns={ledgerColumns as ColumnDef<TallyLedger, unknown>[]}
          globalFilter={search}
        />
      )}
      {!isLoading && tab === "items" && (
        <DataTable<TallyItem>
          data={items}
          columns={itemColumns as ColumnDef<TallyItem, unknown>[]}
          globalFilter={search}
        />
      )}
    </div>
  );
}
