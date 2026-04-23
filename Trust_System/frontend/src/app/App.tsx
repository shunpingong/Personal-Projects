import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import AppShell from "../components/AppShell";
import { authApi, ApiError } from "../services/api";
import { clearSessionTokens, hasSessionTokens, setSessionTokens } from "../services/session";
import DashboardPage from "../pages/DashboardPage";
import ReportsPage from "../pages/ReportsPage";
import UsersPage from "../pages/UsersPage";
import IncidentsPage from "../pages/IncidentsPage";
import AuditLogsPage from "../pages/AuditLogsPage";
import LoginPage from "../pages/LoginPage";
import type { LoginPayload, TokenPair, User } from "../types/api";


interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [sessionReady, setSessionReady] = useState(() => hasSessionTokens());

  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    enabled: sessionReady,
    retry: false,
  });

  useEffect(() => {
    const handleSessionChange = () => {
      setSessionReady(hasSessionTokens());
    };

    const handleAuthExpiry = () => {
      queryClient.clear();
      setSessionReady(false);
    };

    window.addEventListener("trust-system:session-changed", handleSessionChange as EventListener);
    window.addEventListener("trust-system:auth-expired", handleAuthExpiry as EventListener);

    return () => {
      window.removeEventListener(
        "trust-system:session-changed",
        handleSessionChange as EventListener
      );
      window.removeEventListener(
        "trust-system:auth-expired",
        handleAuthExpiry as EventListener
      );
    };
  }, [queryClient]);

  useEffect(() => {
    if (meQuery.error instanceof ApiError && meQuery.error.status === 401) {
      clearSessionTokens();
      setSessionReady(false);
      queryClient.removeQueries({ queryKey: ["auth"] });
    }
  }, [meQuery.error, queryClient]);

  const login = useCallback(
    async (payload: LoginPayload) => {
      const tokens: TokenPair = await authApi.login(payload);
      setSessionTokens(tokens);
      setSessionReady(true);
      return queryClient.fetchQuery({
        queryKey: ["auth", "me"],
        queryFn: authApi.me,
      });
    },
    [queryClient]
  );

  const logout = useCallback(() => {
    clearSessionTokens();
    setSessionReady(false);
    queryClient.clear();
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: meQuery.data ?? null,
      isAuthenticated: sessionReady && Boolean(meQuery.data),
      isLoading: sessionReady ? meQuery.isLoading : false,
      login,
      logout,
    }),
    [login, logout, meQuery.data, meQuery.isLoading, sessionReady]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return context;
}

export function useAuth(): AuthContextValue {
  return useAuthContext();
}

function LoadingState() {
  return (
    <div className="auth-layout">
      <div className="auth-card auth-card--compact">
        <p className="eyebrow">Trust System</p>
        <h1>Loading session</h1>
        <p>Checking your access and restoring the current workspace.</p>
      </div>
    </div>
  );
}

function ProtectedLayout() {
  const auth = useAuth();
  const location = useLocation();

  if (auth.isLoading) {
    return <LoadingState />;
  }

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <AppShell />;
}

function LoginRoute() {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (auth.isAuthenticated) {
      const redirectTarget =
        (location.state as { from?: string } | null)?.from ?? "/dashboard";
      navigate(redirectTarget, { replace: true });
    }
  }, [auth.isAuthenticated, location.state, navigate]);

  if (auth.isLoading) {
    return <LoadingState />;
  }

  return <LoginPage />;
}

function HomeRedirect() {
  const auth = useAuth();

  if (auth.isLoading) {
    return <LoadingState />;
  }

  return <Navigate to={auth.isAuthenticated ? "/dashboard" : "/login"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="/login" element={<LoginRoute />} />
        <Route element={<ProtectedLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/audit-logs" element={<AuditLogsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
