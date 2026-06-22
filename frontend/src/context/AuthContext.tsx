import React, { createContext, useState, useEffect, ReactNode } from 'react';

// Define the shape of our User and Context
interface UserInfo {
  email: string;
  role: string;
}

interface AuthContextType {
  token: string | null;
  user: UserInfo | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);

  // Rehydrate session from localStorage on app load
  useEffect(() => {
    const storedToken = localStorage.getItem('admin_token');
    const storedUser = localStorage.getItem('admin_user');
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const login = async (username: string, password: string) => {
    // FastAPI's OAuth2PasswordRequestForm REQUIRES form-urlencoded data, NOT JSON.
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    // Save to state and storage
    setToken(data.access_token);
    setUser(data.user_info);
    localStorage.setItem('admin_token', data.access_token);
    localStorage.setItem('admin_user', JSON.stringify(data.user_info));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};