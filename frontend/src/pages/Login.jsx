import { useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { Loader2, Lock, Mail } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { GlassCard } from '../components/ui/GlassCard';
import { parseAxiosError } from '../utils/httpError';

export default function Login() {
  const { login, isAuthenticated, loading, token, clearAuthError, error: contextError } = useAuth();
  const location = useLocation();
  const from = location.state?.from?.pathname ?? '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (loading && token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <Loader2 className="h-10 w-10 animate-spin text-gray-500" />
      </div>
    );
  }

  if (!loading && isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const displayError = localError || contextError;

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError('');
    clearAuthError();
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setLocalError(parseAxiosError(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0a0a0a] px-4 pb-16 pt-8">
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-50 md:text-4xl">Nexus Finance Engine</h1>
        <p className="mt-2 text-sm text-gray-400">Institutional ledger and analytics</p>
      </div>

      <GlassCard strong className="w-full max-w-md p-8">
        <h2 className="mb-6 text-center text-lg font-semibold text-gray-50">Sign in</h2>
        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <div>
            <label htmlFor="email" className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-400">
              Email
            </label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-[#0a0a0a] py-3 pl-10 pr-4 text-sm text-gray-50 placeholder:text-gray-600 focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                placeholder="you@company.com"
              />
            </div>
          </div>
          <div>
            <label
              htmlFor="password"
              className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-400"
            >
              Password
            </label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-[#0a0a0a] py-3 pl-10 pr-4 text-sm text-gray-50 placeholder:text-gray-600 focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                placeholder="••••••••"
              />
            </div>
          </div>

          {displayError ? (
            <div
              role="alert"
              className="rounded-lg border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-300"
            >
              {displayError}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-600 bg-gray-800 py-3 text-sm font-semibold text-gray-50 transition hover:bg-gray-700 disabled:opacity-60"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {submitting ? 'Signing in…' : 'Continue'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-400">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="font-medium text-gray-200 underline-offset-2 hover:underline">
            Sign up
          </Link>
        </p>
      </GlassCard>
    </div>
  );
}
