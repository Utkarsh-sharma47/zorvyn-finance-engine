import { Link, Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2, ShieldAlert } from 'lucide-react';

function FullScreenLoader() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#0a0a0a]">
      <Loader2 className="h-12 w-12 animate-spin text-gray-500" aria-hidden />
      <p className="text-sm text-gray-400">Securing your session…</p>
      <span className="sr-only">Loading</span>
    </div>
  );
}

function Forbidden403() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#0a0a0a] px-4">
      <div className="flex max-w-md flex-col items-center gap-4 rounded-xl border border-gray-800 bg-[#111111] p-10 text-center">
        <div className="rounded-lg border border-gray-700 bg-gray-900 p-4 text-gray-300">
          <ShieldAlert className="h-10 w-10" />
        </div>
        <h1 className="text-xl font-semibold text-gray-50">Access denied</h1>
        <p className="text-sm text-gray-400">
          You don&apos;t have permission to view this page. Contact an administrator if you need access.
        </p>
        <Link
          to="/dashboard"
          className="mt-2 rounded-lg border border-gray-600 bg-gray-800 px-6 py-2.5 text-sm font-medium text-gray-50 transition hover:bg-gray-700"
        >
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}

/**
 * @param {object} props
 * @param {string[]} [props.allowedRoles]
 * @param {'redirect' | '403'} [props.roleMismatch]
 * @param {import('react').ReactNode} [props.children]
 */
export default function ProtectedRoute({ allowedRoles, roleMismatch = 'redirect', children }) {
  const { user, loading, isAuthenticated, token } = useAuth();
  const location = useLocation();

  const hasSessionHint = token || (typeof localStorage !== 'undefined' && localStorage.getItem('token'));
  const showLoader = loading && hasSessionHint;

  if (showLoader) {
    return <FullScreenLoader />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (allowedRoles?.length && user && !allowedRoles.includes(user.role)) {
    if (roleMismatch === '403') {
      return <Forbidden403 />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return children ?? <Outlet />;
}
