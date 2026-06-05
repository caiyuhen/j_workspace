import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/axios';
import type { AuthState } from '../types/auth';

interface AuthContextType extends AuthState {
  login: (token: string, refresh: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [auth, setAuth] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: !!localStorage.getItem('access_token'),
  });

  const fetchUser = React.useCallback(async () => {
    try {
      const response = await api.get('/users/me/');
      setAuth({
        user: response.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      setAuth({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        await fetchUser();
      }
    };
    initAuth();
  }, [fetchUser]);

  const login = (token: string, refresh: string) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refresh);
    fetchUser();
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setAuth({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  return (
    <AuthContext.Provider value={{ ...auth, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
