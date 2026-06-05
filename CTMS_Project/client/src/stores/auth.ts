import { create } from 'zustand';

interface User {
  id: string;
  username: string;
  email: string;
  displayName?: string;
  role?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  setUser: (user: User) => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('accessToken'),
  isAuthenticated: !!localStorage.getItem('accessToken'),
  loading: true,

  login: (token: string, user: User) => {
    localStorage.setItem('accessToken', token);
    set({ token, user, isAuthenticated: true, loading: false });
  },

  logout: () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    set({ token: null, user: null, isAuthenticated: false, loading: false });
  },

  setUser: (user: User) => set({ user, isAuthenticated: true, loading: false }),

  setLoading: (loading: boolean) => set({ loading }),
}));
