import { useEffect, useMemo, useState } from 'react';
import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { TrendingDown, TrendingUp, Wallet } from 'lucide-react';
import api from '../services/api';
import { GlassCard } from '../components/ui/GlassCard';
import { KpiSkeleton, Skeleton } from '../components/ui/Skeleton';
import { formatMoney } from '../utils/format';

const PIE_FILLS = ['#6b7280', '#9ca3af', '#4b5563', '#525252', '#737373', '#a3a3a3'];

function parseSummary(raw) {
  if (!raw || typeof raw !== 'object') {
    return { total_income: 0, total_expense: 0, net_revenue: 0 };
  }
  return {
    total_income: Number(raw.total_income ?? 0),
    total_expense: Number(raw.total_expense ?? 0),
    net_revenue: Number(raw.net_revenue ?? 0),
  };
}

/** Normalize API / ORM quirks: enum string, or legacy field names. */
function getTransactionType(t) {
  const raw = t?.transaction_type ?? t?.type ?? t?.transactionType;
  return String(raw ?? '').toLowerCase().trim();
}

function isIncome(t) {
  return getTransactionType(t) === 'income';
}

function isExpense(t) {
  return getTransactionType(t) === 'expense';
}

/** YYYY-MM-DD from ISO datetime or date-only strings. */
function toDayKey(createdAt) {
  if (createdAt == null) return null;
  const s = String(createdAt);
  const day = s.includes('T') ? s.split('T')[0] : s.slice(0, 10);
  if (/^\d{4}-\d{2}-\d{2}$/.test(day)) return day;
  try {
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return null;
    return d.toISOString().slice(0, 10);
  } catch {
    return null;
  }
}

/**
 * Time series for LineChart: one row per calendar day, cumulative income that day.
 */
function buildIncomeByDaySeries(transactions) {
  const map = new Map();
  for (const t of transactions) {
    if (t?.is_deleted) continue;
    if (!isIncome(t)) continue;
    const day = toDayKey(t.created_at);
    if (!day) continue;
    const amt = Number(t.amount);
    if (!Number.isFinite(amt)) continue;
    map.set(day, (map.get(day) ?? 0) + amt);
  }
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, total]) => ({
      date,
      total: Math.round(total * 100) / 100,
    }));
}

/**
 * Pie slices: group expense rows by category string.
 */
function buildExpenseByCategorySeries(transactions) {
  const map = new Map();
  for (const t of transactions) {
    if (t?.is_deleted) continue;
    if (!isExpense(t)) continue;
    const cat = String(t.category ?? 'Uncategorized').trim() || 'Uncategorized';
    const amt = Number(t.amount);
    if (!Number.isFinite(amt) || amt <= 0) continue;
    map.set(cat, (map.get(cat) ?? 0) + amt);
  }
  return [...map.entries()]
    .map(([name, value]) => ({
      name,
      value: Math.round(value * 100) / 100,
    }))
    .sort((a, b) => b.value - a.value);
}

function lineFallbackFromSummary(summary) {
  const s = parseSummary(summary);
  if (s.total_income > 0) {
    return [{ date: 'Summary', total: Math.round(s.total_income * 100) / 100 }];
  }
  return [];
}

function pieFallbackFromSummary(summary) {
  const s = parseSummary(summary);
  if (s.total_expense > 0) {
    return [{ name: 'Total (summary)', value: Math.round(s.total_expense * 100) / 100 }];
  }
  return [];
}

function extractItems(payload) {
  if (!payload?.success || !payload.data) return [];
  const d = payload.data;
  if (Array.isArray(d.items)) return d.items;
  if (Array.isArray(d)) return d;
  return [];
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const [sumRes, txRes] = await Promise.all([
          api.get('/transactions/summary'),
          api.get('/transactions/', { params: { offset: 0, limit: 200 } }),
        ]);
        if (cancelled) return;
        if (sumRes.data?.success) {
          setSummary(sumRes.data.data ?? null);
        }
        setTransactions(extractItems(txRes.data));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const parsedSummary = useMemo(() => parseSummary(summary), [summary]);

  const incomeByDay = useMemo(() => buildIncomeByDaySeries(transactions), [transactions]);
  const expenseByCategory = useMemo(() => buildExpenseByCategorySeries(transactions), [transactions]);

  const lineChartData = useMemo(() => {
    if (incomeByDay.length > 0) return incomeByDay;
    return lineFallbackFromSummary(summary);
  }, [incomeByDay, summary]);

  const pieChartData = useMemo(() => {
    if (expenseByCategory.length > 0) return expenseByCategory;
    return pieFallbackFromSummary(summary);
  }, [expenseByCategory, summary]);

  const lineIsFromLedger = incomeByDay.length > 0;
  const pieIsFromLedger = expenseByCategory.length > 0;

  const lineEmpty = !loading && lineChartData.length === 0;
  const pieEmpty = !loading && pieChartData.length === 0;

  const tooltipStyle = {
    background: '#171717',
    border: '1px solid #404040',
    borderRadius: '8px',
    color: '#e5e5e5',
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-gray-50 md:text-3xl">Analytics</h1>
        <p className="mt-1 text-sm text-gray-400">Performance overview and cash flow</p>
      </header>

      <section className="grid gap-4 sm:grid-cols-3">
        {loading ? (
          <>
            <KpiSkeleton />
            <KpiSkeleton />
            <KpiSkeleton />
          </>
        ) : (
          <>
            <GlassCard className="p-6">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-gray-400">Total income</span>
                <span className="rounded border border-gray-700 bg-gray-800 p-2 text-gray-300">
                  <TrendingUp className="h-4 w-4" />
                </span>
              </div>
              <p className="text-2xl font-semibold tabular-nums text-gray-50">
                {formatMoney(parsedSummary.total_income)}
              </p>
            </GlassCard>
            <GlassCard className="p-6">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-gray-400">Total expenses</span>
                <span className="rounded border border-gray-700 bg-gray-800 p-2 text-gray-300">
                  <TrendingDown className="h-4 w-4" />
                </span>
              </div>
              <p className="text-2xl font-semibold tabular-nums text-gray-50">
                {formatMoney(parsedSummary.total_expense)}
              </p>
            </GlassCard>
            <GlassCard className="p-6">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-gray-400">Net revenue</span>
                <span className="rounded border border-gray-700 bg-gray-800 p-2 text-gray-300">
                  <Wallet className="h-4 w-4" />
                </span>
              </div>
              <p className="text-2xl font-semibold tabular-nums text-gray-50">
                {formatMoney(parsedSummary.net_revenue)}
              </p>
            </GlassCard>
          </>
        )}
      </section>

      <section className="grid gap-6 lg:grid-cols-5">
        <GlassCard className="p-6 lg:col-span-3">
          <h2 className="mb-2 text-sm font-semibold text-gray-50">Revenue over time</h2>
          <p className="mb-4 text-xs text-gray-500">
            Daily income from ledger rows (income type). {lineIsFromLedger ? `${lineChartData.length} day(s)` : 'Using summary fallback if no per-day income.'}
          </p>
          {loading ? (
            <Skeleton className="h-64 w-full rounded-lg" />
          ) : lineEmpty ? (
            <div className="flex h-64 flex-col items-center justify-center rounded-lg border border-dashed border-gray-800 bg-[#0a0a0a] px-4 text-center">
              <p className="text-sm text-gray-400">No income to chart yet</p>
              <p className="mt-1 text-xs text-gray-500">Post income transactions to see a trend by day.</p>
            </div>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineChartData} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#a3a3a3', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#a3a3a3', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `$${v}`}
                  />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value) => [formatMoney(value), 'Income']}
                    labelFormatter={(label) => `Day: ${label}`}
                  />
                  <Line
                    type="monotone"
                    dataKey="total"
                    name="Income"
                    stroke="#d4d4d4"
                    strokeWidth={2}
                    dot={{ fill: '#737373', r: 3 }}
                    activeDot={{ r: 5, fill: '#fafafa' }}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </GlassCard>

        <GlassCard className="p-6 lg:col-span-2">
          <h2 className="mb-2 text-sm font-semibold text-gray-50">Expenses by category</h2>
          <p className="mb-4 text-xs text-gray-500">
            Slices sum expense rows by category. {pieIsFromLedger ? `${pieChartData.length} categories` : 'Using summary if no categorized expenses.'}
          </p>
          {loading ? (
            <Skeleton className="h-64 w-full rounded-lg" />
          ) : pieEmpty ? (
            <div className="flex h-64 flex-col items-center justify-center rounded-lg border border-dashed border-gray-800 bg-[#0a0a0a] px-4 text-center">
              <p className="text-sm text-gray-400">No expenses to chart yet</p>
              <p className="mt-1 text-xs text-gray-500">Post expense transactions with categories to populate the donut.</p>
            </div>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={48}
                    outerRadius={82}
                    paddingAngle={2}
                    stroke="#262626"
                  >
                    {pieChartData.map((entry, i) => (
                      <Cell key={`${entry.name}-${i}`} fill={PIE_FILLS[i % PIE_FILLS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} formatter={(value) => formatMoney(value)} />
                  <Legend
                    wrapperStyle={{ fontSize: '11px', color: '#a3a3a3' }}
                    formatter={(value) => <span className="text-gray-400">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </GlassCard>
      </section>
    </div>
  );
}
