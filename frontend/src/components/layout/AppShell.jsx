import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { BarChart3, BookOpen, LayoutDashboard, LogOut, ScrollText } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const linkClass = ({ isActive }) =>
  [
    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
    isActive
      ? 'border border-gray-600 bg-gray-800 text-gray-50'
      : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200',
  ].join(' ');

export default function AppShell() {
  const navigate = useNavigate();
  const { user, logout, canViewAudit } = useAuth();

  return (
    <div className="flex min-h-screen bg-[#0a0a0a]">
      <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-gray-800 bg-gray-950 px-4 py-6">
        <div className="mb-10 flex items-center gap-3 px-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-gray-700 bg-gray-900">
            <span className="text-xs font-bold tracking-tight text-gray-100">Z</span>
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight text-gray-50">Zorvyn</p>
            <p className="text-[10px] uppercase tracking-widest text-gray-500">Finance</p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-1">
          <NavLink to="/dashboard" className={linkClass}>
            <LayoutDashboard className="h-4 w-4 shrink-0 text-gray-400" />
            Dashboard
          </NavLink>
          <NavLink to="/transactions" className={linkClass}>
            <BookOpen className="h-4 w-4 shrink-0 text-gray-400" />
            Ledger
          </NavLink>
          <NavLink to="/insights" className={linkClass}>
            <BarChart3 className="h-4 w-4 shrink-0 text-gray-400" />
            Insights
          </NavLink>
          {canViewAudit ? (
            <NavLink to="/audit" className={linkClass}>
              <ScrollText className="h-4 w-4 shrink-0 text-gray-400" />
              Audit logs
            </NavLink>
          ) : null}
        </nav>

        <div className="mt-auto space-y-3 border-t border-gray-800 pt-4">
          <div className="rounded-lg border border-gray-800 bg-[#111111] px-3 py-2">
            <p className="truncate text-xs font-medium text-gray-200">{user?.email}</p>
            <p className="text-[10px] text-gray-500">{user?.role}</p>
          </div>
          <button
            type="button"
            onClick={() => {
              logout();
              navigate('/login', { replace: true });
            }}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-700 py-2.5 text-sm text-gray-300 transition hover:bg-gray-900"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      <main className="min-h-screen flex-1 overflow-x-hidden bg-[#0a0a0a] p-6 md:p-10">
        <Outlet />
      </main>
    </div>
  );
}
