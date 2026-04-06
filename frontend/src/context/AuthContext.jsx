import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { API_BASE_URL } from '../config/apiBase';
import api from '../services/api';
import { parseAxiosError } from '../utils/httpError';

const AuthContext = createContext(null);

const AUDIT_ROLES = new Set(['Admin', 'Dev_Admin']);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(!!localStorage.getItem('token'));
  const [error, setError] = useState(null);

  const clearSession = useCallback(() => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setError(null);
  }, []);

  /** @returns {Promise<boolean>} true if the user was loaded */
  const checkAuth = useCallback(async () => {
    const t = localStorage.getItem('token');
    if (!t) {
      setUser(null);
      setLoading(false);
      return false;
    }
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get('/auth/me');
      if (data?.success && data?.data) {
        setUser(data.data);
        setError(null);
        return true;
      }
      const msg = typeof data?.error === 'string' ? data.error : 'Session invalid';
      setError(msg);
      clearSession();
      return false;
    } catch (err) {
      const parsed = parseAxiosError(err);
      setError(parsed);
      clearSession();
      return false;
    } finally {
      setLoading(false);
    }
  }, [clearSession]);

  useEffect(() => {
    if (token) {
      checkAuth();
    } else {
      setUser(null);
      setLoading(false);
    }
  }, [token, checkAuth]);

  const login = useCallback(
    async (email, password) => {
      setError(null);
      try {
        // Do not send a stale Bearer token on the token endpoint (avoids interceptor side effects).
        localStorage.removeItem('token');
        setToken(null);

        // OAuth2PasswordRequestForm: application/x-www-form-urlencoded with username + password.
        const form = new URLSearchParams();
        form.set('username', email.trim());
        form.set('password', password);

        const loginUrl = new URL('auth/login', `${API_BASE_URL}/`);
        const res = await fetch(loginUrl.toString(), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            Accept: 'application/json',
          },
          body: form.toString(),
        });

        let payload = {};
        try {
          payload = await res.json();
        } catch {
          payload = {};
        }

        if (!res.ok) {
          const detail =
            typeof payload.detail === 'string'
              ? payload.detail
              : typeof payload.message === 'string'
                ? payload.message
                : `Login failed (${res.status})`;
          throw new Error(detail);
        }

        // FastAPI: { "access_token": "...", "token_type": "bearer" } — no nested envelope.
        const accessToken = payload.access_token;
        if (typeof accessToken !== 'string' || accessToken.length === 0) {
          throw new Error('No access token in response');
        }

        localStorage.setItem('token', accessToken);
        setToken(accessToken);

        const verified = await checkAuth();
        if (!verified) {
          const msg =
            'Session established but user profile could not be loaded. Verify GET /auth/me against the configured API base URL.';
          setError((prev) => prev || msg);
          throw new Error(msg);
        }
      } catch (err) {
        const msg = parseAxiosError(err);
        setError(msg);
        throw err;
      }
    },
    [checkAuth],
  );

  /**
   * @param {object} data — { email, password, department, role } (matches FastAPI UserRegister)
   */
  const register = useCallback(
    async (data) => {
      setError(null);
      try {
        const { data: body } = await api.post('/auth/register', {
          email: data.email,
          password: data.password,
          department: data.department,
          role: data.role,
        });
        if (!body?.success) {
          const msg = typeof body?.error === 'string' ? body.error : 'Registration failed';
          setError(msg);
          throw new Error(msg);
        }
        await login(data.email, data.password);
      } catch (err) {
        setError(parseAxiosError(err));
        throw err;
      }
    },
    [login],
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const clearAuthError = useCallback(() => setError(null), []);

  const canViewAudit = useMemo(
    () => (user ? AUDIT_ROLES.has(user.role) : false),
    [user],
  );

  /** Inter-account transfers and ledger deletes: Finance Admin only (API enforces the same). */
  const canTransfer = useMemo(() => user?.role === 'Admin', [user]);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      error,
      setError,
      login,
      register,
      logout,
      checkAuth,
      refreshUser: checkAuth,
      clearAuthError,
      isAuthenticated: !!token && !!user,
      canViewAudit,
      canTransfer,
    }),
    [
      token,
      user,
      loading,
      error,
      login,
      register,
      logout,
      checkAuth,
      clearAuthError,
      canViewAudit,
      canTransfer,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
