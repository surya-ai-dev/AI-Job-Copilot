// frontend/src/hooks/useAuth.ts
// Custom React Query hooks managing API transactions for logins, registrations, & token refreshes

import { useMutation } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const useAuth = () => {
  const setAuth = useAuthStore((state) => state.setAuth);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // 1. Login Mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      // API expects form URL-encoded body for oauth2 compatibility
      const details = new URLSearchParams();
      details.append('username', credentials.email);
      details.append('password', credentials.password);

      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: details,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to authenticate user.');
      }

      const tokens = await response.json(); // returns access_token, refresh_token
      
      // Load user profile details
      const userResponse = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${tokens.access_token}` },
      });

      if (!userResponse.ok) {
        throw new Error('Failed to retrieve user profile.');
      }

      const userData = await userResponse.json();
      setAuth(userData, tokens.access_token, tokens.refresh_token);
      return userData;
    },
  });

  // 2. Register Mutation
  const registerMutation = useMutation({
    mutationFn: async (userData: { email: string; password: string; first_name: string; last_name: string }) => {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to register account.');
      }

      return response.json();
    },
  });

  // 3. Logout Helper
  const logout = async () => {
    const refreshToken = useAuthStore.getState().refreshToken;
    if (refreshToken) {
      try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch (err) {
        console.error('Logout request failed:', err);
      }
    }
    clearAuth();
  };

  return {
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error ? (loginMutation.error as Error).message : null,
    
    register: registerMutation.mutateAsync,
    isRegistering: registerMutation.isPending,
    registerError: registerMutation.error ? (registerMutation.error as Error).message : null,
    
    logout,
    user,
    isAuthenticated,
  };
};
