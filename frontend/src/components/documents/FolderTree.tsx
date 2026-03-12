"use client";

import { useState } from "react";
import {
  Folder,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  Plus,
} from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * SIZH CA - Document Vault Folder Tree
 * Renders a nested tree of folders with expand/collapse.
 */

interface DocumentFolder {
  id: string;
  name: string;
  slug: string;
  is_default: boolean;
  file_count: number;
  children: DocumentFolder[];
}

interface FolderTreeProps {
  folders: DocumentFolder[];
  selectedFolderId: string | null;
  onSelectFolder: (folderId: string) => void;
  onCreateFolder?: (parentId?: string | null) => void;
}

function FolderNode({
  folder,
  depth,
  selectedFolderId,
  onSelectFolder,
}: {
  folder: DocumentFolder;
  depth: number;
  selectedFolderId: string | null;
  onSelectFolder: (folderId: string) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = folder.children && folder.children.length > 0;
  const isSelected = selectedFolderId === folder.id;

  return (
    <div>
      <button
        onClick={() => onSelectFolder(folder.id)}
        className={cn(
          "flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors",
          "hover:bg-blue-50",
          isSelected ? "bg-blue-100 text-blue-700 font-medium" : "text-gray-700"
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {hasChildren ? (
          <span
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="p-0.5 cursor-pointer"
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </span>
        ) : (
          <span className="w-4" />
        )}

        {isExpanded && hasChildren ? (
          <FolderOpen className="h-4 w-4 text-blue-500" />
        ) : (
          <Folder className="h-4 w-4 text-yellow-500" />
        )}

        <span className="flex-1 text-left truncate">{folder.name}</span>

        {folder.file_count > 0 && (
          <span className="rounded-full bg-gray-200 px-1.5 py-0.5 text-xs text-gray-600">
            {folder.file_count}
          </span>
        )}
      </button>

      {isExpanded && hasChildren && (
        <div>
          {folder.children.map((child) => (
            <FolderNode
              key={child.id}
              folder={child}
              depth={depth + 1}
              selectedFolderId={selectedFolderId}
              onSelectFolder={onSelectFolder}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FolderTree({
  folders,
  selectedFolderId,
  onSelectFolder,
  onCreateFolder,
}: FolderTreeProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between px-2 py-2">
        <h3 className="text-xs font-semibold uppercase text-gray-400">Folders</h3>
        <button
          onClick={() => onCreateFolder?.(null)}
          title="New folder"
          className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
        </button>
      </div>
      {folders.map((folder) => (
        <FolderNode
          key={folder.id}
          folder={folder}
          depth={0}
          selectedFolderId={selectedFolderId}
          onSelectFolder={onSelectFolder}
        />
      ))}
    </div>
  );
}
