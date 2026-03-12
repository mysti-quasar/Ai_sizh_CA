import { create } from "zustand";
import { persist } from "zustand/middleware";
import api from "@/lib/api";

/**
 * SIZH CA - Auth Store (Zustand)
 * Manages authentication state: user, tokens, login/logout.
 */

interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  firm_name: string | null;
  is_verified: boolean;
  active_client_profile_id: string | null;
}

interface RegisterData {
  email: string;
  username: string;
  first_name: string;
  last_name?: string;
  phone?: string;
  firm_name?: string;
  password: string;
  password_confirm: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const { data } = await api.post("/auth/login/", { email, password });
          localStorage.setItem("access_token", data.access);
          localStorage.setItem("refresh_token", data.refresh);
          const profileRes = await api.get("/auth/profile/");
          set({
            user: profileRes.data,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, isAuthenticated: false });
      },

      fetchProfile: async () => {
        try {
          const { data } = await api.get("/auth/profile/");
          set({ user: data, isAuthenticated: true });
        } catch {
          set({ user: null, isAuthenticated: false });
        }
      },

      register: async (registerData) => {
        set({ isLoading: true });
        try {
          await api.post("/auth/register/", registerData);
          set({ isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },
    }),
    {
      name: "sizh-ca-auth",
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
