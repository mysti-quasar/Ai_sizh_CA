"use client";

import {
  FileText,
  FileSpreadsheet,
  Image as ImageIcon,
  File,
  Upload,
  MoreVertical,
} from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * SIZH CA - Document Vault File List
 * Displays files within a selected folder.
 */

interface DocumentFile {
  id: string;
  name: string; // mapped from original_filename by serializer
  file_type: string;
  file_size: number;
  processing_status: string;
  uploaded_at: string;
}

interface FileListProps {
  files: DocumentFile[];
  folderName: string | null;
  onUpload?: () => void;
}

const fileIcons: Record<string, React.ElementType> = {
  pdf: FileText,
  excel: FileSpreadsheet,
  image: ImageIcon,
  csv: FileSpreadsheet,
  other: File,
};

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function FileList({ files, folderName, onUpload }: FileListProps) {
  if (!folderName) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-400">
        Select a folder to view files
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">{folderName}</h2>
        <button
          onClick={onUpload}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          <Upload className="h-4 w-4" />
          Upload
        </button>
      </div>

      {/* File list */}
      {files.length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 text-gray-400">
          <Upload className="h-8 w-8 mb-2" />
          <p className="text-sm">No files in this folder</p>
          <p className="text-xs">Drag & drop or click Upload</p>
        </div>
      ) : (
        <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="px-4 py-3 text-left font-medium text-gray-500">Name</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Type</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Size</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => {
                const Icon = fileIcons[file.file_type] || File;
                return (
                  <tr key={file.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 flex items-center gap-2">
                      <Icon className="h-4 w-4 text-gray-400 shrink-0" />
                      <span className="truncate max-w-[200px]">{file.name}</span>
                    </td>
                    <td className="px-4 py-3 uppercase text-gray-500">{file.file_type}</td>
                    <td className="px-4 py-3 text-gray-500">{formatFileSize(file.file_size)}</td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          statusColors[file.processing_status] || "bg-gray-100 text-gray-600"
                        )}
                      >
                        {file.processing_status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{formatDate(file.uploaded_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <button className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors">
                        <MoreVertical className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
