import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { login as apiLogin, getCurrentUser, logout as apiLogout } from '../api/authApi';

export interface UserInfo {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'user' | 'auditor' | 'developer';
  firstName?: string;
  lastName?: string;
  avatar?: string;
}

interface AuthState {
  user: UserInfo | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  
  // Actions
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: UserInfo | null) => void;
  setToken: (token: string | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false,

      // Login action
      login: async (username: string, password: string) => {
        set({ loading: true });
        try {
          const response = await apiLogin(username, password);
          const { token, user } = response;
          
          // Store token in localStorage
          localStorage.setItem('auth_token', token);
          
          set({
            token,
            user,
            isAuthenticated: true,
            loading: false,
          });
        } catch (error) {
          set({ loading: false });
          throw error;
        }
      },

      // Logout action
      logout: async () => {
        try {
          await apiLogout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          // Clear all auth data
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_info');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          });
          // Redirect to login page
          window.location.href = '/login';
        }
      },

      // Check authentication status on app load
      checkAuth: async () => {
        const token = localStorage.getItem('auth_token');
        if (!token) {
          set({ isAuthenticated: false, loading: false });
          return;
        }

        set({ token, loading: true });
        try {
          const user = await getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            loading: false,
          });
        } catch (error) {
          console.error('Auth check failed:', error);
          // Token invalid, clear and redirect
          localStorage.removeItem('auth_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
          });
        }
      },

      // Set user manually
      setUser: (user) => set({ user }),

      // Set token manually
      setToken: (token) => set({ token }),
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({ 
        token: state.token, 
        user: state.user,
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);

export default useAuthStore;
