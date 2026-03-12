"use client";

import { useEffect, useState, useCallback } from "react";
import { FolderOpen, Plus, X } from "lucide-react";
import FolderTree from "@/components/documents/FolderTree";
import FileList from "@/components/documents/FileList";
import UploadFileModal from "@/components/documents/UploadFileModal";
import { useDocumentStore } from "@/store/document-store";
import { useClientStore } from "@/store/client-store";

/**
 * SIZH CA - Document Vault Page
 * Live folder + file manager wired to the backend.
 */

export default function DocumentVaultPage() {
  const { activeClient } = useClientStore();
  const {
    folders,
    selectedFolderId,
    files,
    isLoadingFolders,
    isLoadingFiles,
    isUploading,
    fetchFolders,
    initDefaultFolders,
    createFolder,
    selectFolder,
    uploadFile,
  } = useDocumentStore();

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showNewFolderModal, setShowNewFolderModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [newFolderParentId, setNewFolderParentId] = useState<string | null>(null);

  // On mount: load folders; if none exist, initialize defaults
  useEffect(() => {
    fetchFolders().then(() => {
      const { folders: loaded } = useDocumentStore.getState();
      if (loaded.length === 0) {
        initDefaultFolders();
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeClient?.id]);

  const selectedFolder = folders.find((f) => f.id === selectedFolderId);

  const handleCreateFolder = useCallback(
    (parentId?: string | null) => {
      setNewFolderParentId(parentId ?? null);
      setNewFolderName("");
      setShowNewFolderModal(true);
    },
    []
  );

  const handleSubmitNewFolder = async () => {
    const trimmed = newFolderName.trim();
    if (!trimmed) return;
    await createFolder(trimmed, newFolderParentId);
    setShowNewFolderModal(false);
  };

  const handleUpload = async (file: File): Promise<boolean> => {
    if (!selectedFolderId) return false;
    return await uploadFile(selectedFolderId, file);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
            <FolderOpen className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Document Vault</h1>
            <p className="text-sm text-gray-500">
              {activeClient
                ? `${activeClient.name} — structured document storage`
                : "Select a client to manage documents"}
            </p>
          </div>
        </div>
        {activeClient && (
          <button
            onClick={() => handleCreateFolder(null)}
            className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Folder
          </button>
        )}
      </div>

      {/* No client selected */}
      {!activeClient && (
        <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <FolderOpen className="h-5 w-5 shrink-0" />
          No active client selected. Please create or select a client to use the Document Vault.
        </div>
      )}

      {/* Two-column layout: Folders | Files */}
      {activeClient && (
        <div className="flex gap-6 min-h-[500px]">
          {/* Left: Folder Tree */}
          <div className="w-64 shrink-0 rounded-xl border border-gray-200 bg-white p-3">
            {isLoadingFolders ? (
              <div className="flex items-center justify-center py-8 text-gray-400 text-sm">
                Loading folders…
              </div>
            ) : (
              <FolderTree
                folders={folders}
                selectedFolderId={selectedFolderId}
                onSelectFolder={selectFolder}
                onCreateFolder={handleCreateFolder}
              />
            )}
          </div>

          {/* Right: File List */}
          <div className="flex-1 rounded-xl border border-gray-200 bg-white p-4">
            {isLoadingFiles ? (
              <div className="flex h-48 items-center justify-center text-gray-400 text-sm">
                Loading files…
              </div>
            ) : (
              <FileList
                files={files}
                folderName={selectedFolder?.name ?? null}
                onUpload={() => setShowUploadModal(true)}
              />
            )}
          </div>
        </div>
      )}

      {/* Upload File Modal */}
      {showUploadModal && selectedFolder && (
        <UploadFileModal
          folderName={selectedFolder.name}
          isUploading={isUploading}
          onUpload={handleUpload}
          onClose={() => setShowUploadModal(false)}
        />
      )}

      {/* New Folder Modal */}
      {showNewFolderModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-900">New Folder</h2>
              <button
                onClick={() => setShowNewFolderModal(false)}
                className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  Folder Name
                </label>
                <input
                  type="text"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSubmitNewFolder()}
                  placeholder="e.g. Invoices 2024"
                  autoFocus
                  className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 border-t border-gray-100 px-6 py-4">
              <button
                onClick={() => setShowNewFolderModal(false)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitNewFolder}
                disabled={!newFolderName.trim()}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Plus className="h-4 w-4" />
                Create Folder
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
