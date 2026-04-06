import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import { parseAxiosError } from '../utils/httpError';

const AuthContext = createContext(null);

const AUDIT_ROLES = new Set(['Admin', 'Dev_Admin']);

/**
 * OAuth2 password flow: body MUST be application/x-www-form-urlencoded
 * with fields `username` (email) and `password`. Send a string body so Axios
 * does not JSON-serialize or alter the payload.
 */
function buildLoginFormBody(email, password) {
  const params = new URLSearchParams();
  params.append('username', email.trim());
  params.append('password', password);
  return params.toString();
}

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
        const body = buildLoginFormBody(email, password);
        const { data } = await api.post('/auth/login', body, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        });
        const accessToken = data?.access_token;
        if (!accessToken) throw new Error('No access token in response');
        
        localStorage.setItem('token', accessToken);
        setToken(accessToken);
        
        const verified = await checkAuth();
        if (!verified) {
          const msg =
            'Signed in but could not load your profile (GET /auth/me). Confirm the backend route exists and the Vite proxy forwards /api to port 8000.';
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
