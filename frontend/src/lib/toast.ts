import { toast } from "sonner";
import axios from "axios";

/**
 * SIZH CA - Global Toast Utility
 * Wraps sonner with SIZH-specific helpers and standardised error format.
 * Format: "[Error XXX] - Simple explanation"
 */

export const toastSuccess = (message: string) =>
  toast.success(message, { duration: 3500 });

export const toastError = (message: string) =>
  toast.error(message, { duration: 6000 });

export const toastInfo = (message: string) =>
  toast.info(message, { duration: 4000 });

export const toastLoading = (message: string) =>
  toast.loading(message);

export const toastDismiss = (id?: string | number) =>
  toast.dismiss(id);

/**
 * Extracts a user-friendly error message from an Axios or unknown error.
 * Format: "[Error STATUS] - EXPLANATION"
 */
export function extractApiError(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const data = error.response?.data;

    // Try to get a clean backend message
    const detail =
      data?.detail ||
      data?.error ||
      data?.message ||
      (typeof data === "string" ? data : null);

    const explanation = detail || fallback;

    if (status) {
      return `Error ${status} — ${explanation}`;
    }
    // Network error
    return "Network Error — Could not reach the server. Check your connection.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}

/**
 * Show a toast for any caught error.
 * Logs technical details to console.
 */
export function toastApiError(error: unknown, context?: string): void {
  // Always log full details for developers
  console.error(`[SIZH CA Error]${context ? ` (${context})` : ""}`, error);
  toastError(extractApiError(error));
}
