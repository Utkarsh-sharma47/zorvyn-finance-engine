import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
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
        // OAuth2PasswordRequestForm: form fields must be `username` (email) and `password`.
        const formData = new URLSearchParams();
        formData.append('username', email.trim());
        formData.append('password', password);
        const body = formData.toString();

        const response = await api.post('/auth/login', body, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        });

        // FastAPI returns the OAuth2 token payload directly (no success/data envelope).
        const accessToken = response.data?.access_token;
        if (typeof accessToken !== 'string' || accessToken.length === 0) {
          throw new Error('No access token in response');
        }

        localStorage.setItem('token', accessToken);
        setToken(accessToken);

        const verified = await checkAuth();
        if (!verified) {
          const msg =
            'Session established but user profile could not be loaded. Verify GET /api/v1/auth/me and API connectivity.';
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
