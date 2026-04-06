import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { Building2, Loader2, Lock, Mail, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { GlassCard } from '../components/ui/GlassCard';

const DEPARTMENTS = [
  { value: 'Finance', label: 'Finance' },
  { value: 'Engineering', label: 'Engineering' },
];

const ROLES = [
  { value: 'Admin', label: 'Admin' },
  { value: 'Analyst', label: 'Analyst' },
  { value: 'Viewer', label: 'Viewer' },
  { value: 'Dev_Admin', label: 'Dev Admin' },
  { value: 'Dev_Employee', label: 'Dev Employee' },
];

const inputClass =
  'w-full rounded-lg border border-gray-700 bg-[#0a0a0a] py-3 pl-10 pr-4 text-sm text-gray-50 placeholder:text-gray-600 focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500';

export default function Register() {
  const { register, isAuthenticated, loading, token, clearAuthError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [department, setDepartment] = useState('Finance');
  const [role, setRole] = useState('Viewer');
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
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError('');
    clearAuthError();
    setSubmitting(true);
    try {
      await register({ email, password, department, role });
    } catch (err) {
      const d = err.response?.data;
      const msg =
        (typeof d?.error === 'string' && d.error) ||
        (typeof err.message === 'string' && err.message) ||
        'Registration failed';
      setLocalError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0a0a0a] px-4 pb-16 pt-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-50 md:text-4xl">Create account</h1>
        <p className="mt-2 text-sm text-gray-400">Join your team on Zorvyn Finance</p>
      </div>

      <GlassCard strong className="w-full max-w-md p-8">
        <h2 className="mb-6 text-center text-lg font-semibold text-gray-50">Sign up</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="reg-email" className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-400">
              Work email
            </label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <input
                id="reg-email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
                placeholder="you@company.com"
              />
            </div>
          </div>

          <div>
            <label htmlFor="reg-password" className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-400">
              Password
            </label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <input
                id="reg-password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputClass}
                placeholder="At least 8 characters"
              />
            </div>
          </div>

          <div>
            <label htmlFor="department" className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-400">
              Department
            </label>
            <div className="relative">
              <Building2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <select
                id="department"
                name="department"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className={`${inputClass} appearance-none`}
              >
                {DEPARTMENTS.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="role" className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-gray-400">
              Role
            </label>
            <div className="relative">
              <Shield className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
              <select
                id="role"
                name="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className={`${inputClass} appearance-none`}
              >
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {localError ? (
            <p className="rounded-lg border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-300">{localError}</p>
          ) : null}

          <button
            type="submit"
            disabled={submitting}
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg border border-gray-600 bg-gray-800 py-3 text-sm font-semibold text-gray-50 transition hover:bg-gray-700 disabled:opacity-60"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-gray-200 underline-offset-2 hover:underline">
            Log in
          </Link>
        </p>
      </GlassCard>
    </div>
  );
}
