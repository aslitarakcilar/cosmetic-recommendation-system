"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { api, type UserProfile } from "../lib/api";
import { isAdminEmail } from "../lib/admin";

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: (token: string) => Promise<void>;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "sephora_token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    async function bootstrapAuth() {
      const stored = localStorage.getItem(TOKEN_KEY);

      if (!stored) {
        setState({ user: null, token: null, loading: false });
        return;
      }

      try {
        const user = await api.getMe(stored);
        if (!cancelled) {
          setState({ user, token: stored, loading: false });
        }
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        if (!cancelled) {
          setState({ user: null, token: null, loading: false });
        }
      }
    }

    bootstrapAuth();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (token: string) => {
    const user = await api.getMe(token);
    localStorage.setItem(TOKEN_KEY, token);
    setState({ user, token, loading: false });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setState({ user: null, token: null, loading: false });
  }, []);

  const refreshUser = useCallback(async (token: string) => {
    const user = await api.getMe(token);
    setState((prev) => ({ ...prev, user }));
  }, []);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        refreshUser,
        isAdmin: isAdminEmail(state.user?.email),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
