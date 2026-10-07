import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: number;
  username: string;
  role: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
  checkAuth: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,

      setAuth: (token, user) => {
        localStorage.setItem("token", token);
        set({ user, isAuthenticated: true });
      },

      logout: () => {
        localStorage.removeItem("token");
        set({ user: null, isAuthenticated: false });
      },

      checkAuth: () => {
        const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
        const state = get();

        if (token && state.user) {
          if (!state.isAuthenticated) {
            set({ isAuthenticated: true });
          }
          return true;
        } else {
          if (state.isAuthenticated) {
            set({ isAuthenticated: false, user: null });
            if (typeof window !== "undefined") localStorage.removeItem("token");
          }
          return false;
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ user: state.user }), // Only persist user data
      onRehydrateStorage: () => (state) => {
        // After rehydration, sync isAuthenticated with token presence to avoid flash
        if (state) {
          const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
          state.isAuthenticated = !!(token && state.user);
        }
      },
    }
  )
);
