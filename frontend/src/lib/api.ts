import axios from "axios";

/**
 * SIZH CA - Axios API Client
 * Configured with JWT interceptors for the Django backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Request interceptor: attach JWT access token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 (refresh) + push all other errors to toast
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) throw new Error("No refresh token");

        const { data } = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        localStorage.setItem("access_token", data.access);
        if (data.refresh) {
          localStorage.setItem("refresh_token", data.refresh);
        }

        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    // Show a global toast for all non-401 errors (not auth errors, not cancelled requests)
    if (error.response?.status !== 401 && !axios.isCancel(error)) {
      const status = error.response?.status;
      const data = error.response?.data;
      const detail =
        data?.detail ||
        data?.error ||
        data?.message ||
        (typeof data === "string" && data.length < 200 ? data : null);

      const explanation = detail || "An unexpected error occurred. Please try again.";
      const msg = status ? `Error ${status} — ${explanation}` : `Network Error — Could not reach the server.`;

      // Dynamically import toast so this module stays server-safe
      import("sonner").then(({ toast }) => toast.error(msg, { duration: 6000 })).catch(() => {});
      console.error(`[SIZH CA API Error] ${msg}`, error);
    }

    return Promise.reject(error);
  }
);

export default api;
