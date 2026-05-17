import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '../utils/api';

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  token: string | null;
  publicKey: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = sessionStorage.getItem('token');
    const storedUsername = sessionStorage.getItem('username');
    const storedPublicKey = sessionStorage.getItem('publicKey');

    if (storedToken && storedUsername) {
      setToken(storedToken);
      setUsername(storedUsername);
      setPublicKey(storedPublicKey);
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const login = async (user: string, pass: string) => {
    const response = await authApi.login(user, pass);
    sessionStorage.setItem('token', response.token);
    sessionStorage.setItem('username', response.username);
    sessionStorage.setItem('publicKey', response.public_key);
    setToken(response.token);
    setUsername(response.username);
    setPublicKey(response.public_key);
    setIsAuthenticated(true);
  };

  const register = async (user: string, pass: string) => {
    await authApi.register(user, pass);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
    } finally {
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('username');
      sessionStorage.removeItem('publicKey');
      setToken(null);
      setUsername(null);
      setPublicKey(null);
      setIsAuthenticated(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        username,
        token,
        publicKey,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
