// frontend/src/store/authStore.ts
// Zustand store for managing client-side authentication states and JWT tokens

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface UserState {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
}

interface AuthStore {
  user: UserState | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: UserState, accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
  updateUser: (first_name: string, last_name: string) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      setAuth: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken, isAuthenticated: true }),
      clearAuth: () =>
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),
      updateUser: (first_name, last_name) =>
        set((state) => ({
          user: state.user ? { ...state.user, first_name, last_name } : null,
        })),
    }),
    {
      name: 'auth-storage', // name of the item in the storage (defaults to localStorage)
      storage: createJSONStorage(() => localStorage),
    }
  )
);
