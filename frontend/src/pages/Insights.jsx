import { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Loader2 } from 'lucide-react';
import api from '../services/api';
import { GlassCard } from '../components/ui/GlassCard';
import { formatDate, formatMoney } from '../utils/format';

const HIGH_VALUE_MIN = 500;

function parseSummary(raw) {
  if (!raw || typeof raw !== 'object') {
    return { total_income: 0, total_expense: 0 };
  }
  return {
    total_income: Number(raw.total_income ?? 0),
    total_expense: Number(raw.total_expense ?? 0),
  };
}

export default function Insights() {
  const [summary, setSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const sumRes = await api.get('/transactions/summary');
        if (!cancelled && sumRes.data?.success) {
          setSummary(sumRes.data.data ?? null);
        }
      } catch {
        if (!cancelled) setSummary(null);
      }
      try {
        const txRes = await api.get('/transactions/', { params: { offset: 0, limit: 200 } });
        if (!cancelled && txRes.data?.success && txRes.data.data?.items) {
          setTransactions(txRes.data.data.items);
        }
      } catch {
        if (!cancelled) setTransactions([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const parsed = useMemo(() => parseSummary(summary), [summary]);

  /** Recharts expects rows with stable keys: `name` (category) + `amount` (bar height). */
  const chartData = useMemo(
    () => [
      { name: 'Income', amount: parsed.total_income },
      { name: 'Expenses', amount: parsed.total_expense },
    ],
    [parsed.total_income, parsed.total_expense],
  );

  const highValueRows = useMemo(() => {
    return transactions
      .filter((t) => !t.is_deleted && Number(t.amount) > HIGH_VALUE_MIN)
      .sort((a, b) => Number(b.amount) - Number(a.amount))
      .slice(0, 25);
  }, [transactions]);

  const tooltipStyle = {
    background: '#171717',
    border: '1px solid #404040',
    borderRadius: '8px',
    color: '#e5e5e5',
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-gray-50 md:text-3xl">Insights</h1>
        <p className="mt-1 text-sm text-gray-400">
          Analyst view — income vs expenses and high-value ledger activity (over {formatMoney(HIGH_VALUE_MIN)})
        </p>
      </header>

      <GlassCard className="p-6">
        <h2 className="mb-6 text-sm font-semibold text-gray-50">Income vs expenses</h2>
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          </div>
        ) : (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#a3a3a3', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fill: '#a3a3a3', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${v}`}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value) => formatMoney(value)}
                  labelFormatter={(label) => String(label)}
                />
                <Bar dataKey="amount" fill="#ffffff" radius={[4, 4, 0, 0]} stroke="#404040" strokeWidth={1} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </GlassCard>

      <GlassCard className="overflow-hidden p-0">
        <div className="border-b border-gray-800 px-6 py-4">
          <h2 className="text-sm font-semibold text-gray-50">Recent high-value transactions</h2>
          <p className="mt-1 text-xs text-gray-400">Amount strictly greater than {formatMoney(HIGH_VALUE_MIN)}</p>
        </div>
        <div className="max-h-[480px] overflow-x-auto overflow-y-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs uppercase tracking-wider text-gray-400">
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-3 font-medium">ID</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-3 font-medium">Type</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-3 font-medium">Amount</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-3 font-medium">Category</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-3 font-medium">Account</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-3 font-medium">When</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-gray-400">
                    <Loader2 className="mx-auto h-8 w-8 animate-spin text-gray-500" />
                  </td>
                </tr>
              ) : highValueRows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-gray-400">
                    No transactions above {formatMoney(HIGH_VALUE_MIN)}
                  </td>
                </tr>
              ) : (
                highValueRows.map((row) => (
                  <tr key={row.id} className="border-b border-gray-800/80 hover:bg-gray-900/50">
                    <td className="px-5 py-3 font-mono text-xs text-gray-400">{row.id}</td>
                    <td className="px-5 py-3 text-gray-300">{String(row.transaction_type)}</td>
                    <td className="px-5 py-3 tabular-nums text-gray-50">{formatMoney(row.amount)}</td>
                    <td className="px-5 py-3 text-gray-300">{row.category}</td>
                    <td className="px-5 py-3 font-mono text-xs text-gray-400">{row.account_id}</td>
                    <td className="px-5 py-3 text-gray-400">{formatDate(row.created_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}
