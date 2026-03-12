/**
 * SIZH CA - Document Vault Zustand Store
 * Manages folders, selected folder, files, and upload state.
 */

import { create } from "zustand";
import api from "@/lib/api";
import { toastSuccess, toastApiError } from "@/lib/toast";

export interface DocumentFolder {
  id: string;
  name: string;
  slug: string;
  is_default: boolean;
  default_type: string | null;
  file_count: number;
  children: DocumentFolder[];
}

export interface DocumentFile {
  id: string;
  name: string; // original_filename via serializer
  file_type: string;
  file_size: number;
  processing_status: string;
  uploaded_at: string;
}

interface DocumentState {
  folders: DocumentFolder[];
  selectedFolderId: string | null;
  files: DocumentFile[];
  isLoadingFolders: boolean;
  isLoadingFiles: boolean;
  isUploading: boolean;

  // Actions
  fetchFolders: () => Promise<void>;
  initDefaultFolders: () => Promise<void>;
  createFolder: (name: string, parentId?: string | null) => Promise<void>;
  selectFolder: (folderId: string) => void;
  fetchFiles: (folderId: string) => Promise<void>;
  uploadFile: (folderId: string, file: File) => Promise<boolean>;
  resetFiles: () => void;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  folders: [],
  selectedFolderId: null,
  files: [],
  isLoadingFolders: false,
  isLoadingFiles: false,
  isUploading: false,

  fetchFolders: async () => {
    set({ isLoadingFolders: true });
    try {
      const res = await api.get("/documents/folders/");
      set({ folders: res.data.results ?? res.data });
    } catch (err) {
      toastApiError(err, "fetching folders");
    } finally {
      set({ isLoadingFolders: false });
    }
  },

  initDefaultFolders: async () => {
    try {
      await api.post("/documents/init-folders/");
      await get().fetchFolders();
    } catch (err) {
      toastApiError(err, "initializing default folders");
    }
  },

  createFolder: async (name: string, parentId?: string | null) => {
    try {
      const payload: Record<string, unknown> = { name };
      if (parentId) payload.parent = parentId;
      await api.post("/documents/folders/create/", payload);
      toastSuccess(`Folder "${name}" created`);
      await get().fetchFolders();
    } catch (err) {
      toastApiError(err, "creating folder");
    }
  },

  selectFolder: (folderId: string) => {
    set({ selectedFolderId: folderId, files: [] });
    get().fetchFiles(folderId);
  },

  fetchFiles: async (folderId: string) => {
    set({ isLoadingFiles: true });
    try {
      const res = await api.get(`/documents/folders/${folderId}/files/`);
      set({ files: res.data.results ?? res.data });
    } catch (err) {
      toastApiError(err, "fetching files");
    } finally {
      set({ isLoadingFiles: false });
    }
  },

  uploadFile: async (folderId: string, file: File): Promise<boolean> => {
    set({ isUploading: true });
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post(`/documents/folders/${folderId}/files/upload/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toastSuccess(`"${file.name}" uploaded successfully`);
      await get().fetchFiles(folderId);
      return true;
    } catch (err) {
      toastApiError(err, "uploading file");
      return false;
    } finally {
      set({ isUploading: false });
    }
  },

  resetFiles: () => set({ files: [] }),
}));
