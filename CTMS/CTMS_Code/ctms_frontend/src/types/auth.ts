export interface User {
  id: number;
  username: string;
  email: string;
  role: 'PM' | 'CRA' | 'DM' | 'STAT' | 'PV' | 'QA' | 'INV' | 'IRB' | 'ADMIN';
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthContextType extends AuthState {
  login: (token: string, refresh: string) => void;
  logout: () => void;
}
