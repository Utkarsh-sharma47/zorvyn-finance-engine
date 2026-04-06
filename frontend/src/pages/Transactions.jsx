import { useCallback, useEffect, useState } from 'react';
import { ArrowRightLeft, ChevronLeft, ChevronRight, Loader2, Trash2 } from 'lucide-react';
import api from '../services/api';
import { GlassCard } from '../components/ui/GlassCard';
import Modal from '../components/ui/Modal';
import { formatDate, formatMoney } from '../utils/format';
import { useAuth } from '../context/AuthContext';
import { parseAxiosError } from '../utils/httpError';

const MS_PER_SEC = 1000;

/** Matches backend transfer twin: same category, user, amount magnitude, within 1s. */
function transferTwinMatch(a, b) {
  if (!a || !b || a.id === b.id) return false;
  if (String(a.category ?? '').toLowerCase() !== 'transfer') return false;
  if (String(b.category ?? '').toLowerCase() !== 'transfer') return false;
  if (Number(a.user_id) !== Number(b.user_id)) return false;
  if (Number(a.amount) !== Number(b.amount)) return false;
  const ta = new Date(a.created_at).getTime();
  const tb = new Date(b.created_at).getTime();
  if (Number.isNaN(ta) || Number.isNaN(tb)) return false;
  return Math.abs(ta - tb) <= MS_PER_SEC;
}

const PAGE_SIZE = 10;

function TypeBadge({ type }) {
  const income = String(type ?? '').toLowerCase() === 'income';
  return (
    <span
      className={`inline-flex rounded px-2 py-0.5 text-xs font-medium ${
        income
          ? 'border border-gray-600 bg-gray-800 text-gray-200'
          : 'border border-gray-700 bg-gray-900 text-gray-300'
      }`}
    >
      {income ? 'Income' : 'Expense'}
    </span>
  );
}

export default function Transactions() {
  const { canTransfer } = useAuth();
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [fromId, setFromId] = useState('');
  const [toId, setToId] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('Transfer');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/transactions/', {
        params: { offset, limit: PAGE_SIZE },
      });
      if (data?.success && data.data) {
        setRows(data.data.items ?? []);
        setTotal(data.data.total ?? 0);
      }
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    load();
  }, [load]);

  const openModal = async () => {
    setFormError('');
    setModalOpen(true);
    try {
      const { data } = await api.get('/accounts/');
      if (data?.success && data.data?.items) {
        setAccounts(data.data.items);
        if (data.data.items.length >= 2) {
          setFromId(String(data.data.items[0].id));
          setToId(String(data.data.items[1].id));
        } else if (data.data.items.length === 1) {
          setFromId(String(data.data.items[0].id));
          setToId('');
        }
      }
    } catch {
      setAccounts([]);
    }
  };

  const handleDelete = useCallback(
    async (id) => {
      setDeleteError('');
      const snapshot = rows.find((r) => r.id === id);
      setDeletingId(id);
      try {
        await api.delete(`/transactions/${id}`);
        const twinIds = new Set([id]);
        if (snapshot) {
          for (const r of rows) {
            if (r.id !== id && transferTwinMatch(snapshot, r)) {
              twinIds.add(r.id);
            }
          }
        }
        setRows((prev) => prev.filter((r) => !twinIds.has(r.id)));
        setTotal((t) => Math.max(0, t - twinIds.size));
      } catch (err) {
        setDeleteError(parseAxiosError(err));
      } finally {
        setDeletingId(null);
      }
    },
    [rows],
  );

  async function submitTransfer(e) {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    try {
      await api.post('/transactions/transfer', {
        from_account_id: Number(fromId),
        to_account_id: Number(toId),
        amount: amount,
        description: description || 'Transfer',
      });
      setModalOpen(false);
      setAmount('');
      await load();
    } catch (err) {
      const msg = err.response?.data?.error ?? err.response?.data?.detail ?? 'Transfer failed';
      setFormError(typeof msg === 'string' ? msg : 'Transfer failed');
    } finally {
      setSubmitting(false);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const page = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-50">General Ledger</h1>
          <p className="mt-1 text-sm text-gray-400">All posted transactions</p>
        </header>
        {canTransfer ? (
          <button
            type="button"
            onClick={openModal}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-gray-600 bg-gray-800 px-4 py-2.5 text-sm font-medium text-gray-50 transition hover:bg-gray-700"
          >
            <ArrowRightLeft className="h-4 w-4" />
            New transfer
          </button>
        ) : null}
      </div>

      {deleteError ? (
        <p className="text-sm text-red-400" role="alert">
          {deleteError}
        </p>
      ) : null}

      <GlassCard className="overflow-hidden">
        <div className="max-h-[600px] overflow-x-auto overflow-y-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs uppercase tracking-wider text-gray-400">
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-4 font-medium">ID</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-4 font-medium">Type</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-4 font-medium">Amount</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-4 font-medium">Category</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-4 font-medium">Account</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-4 font-medium">When</th>
                <th className="sticky top-0 z-10 bg-[#111111] px-5 py-4 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-16 text-center text-gray-400">
                    <Loader2 className="mx-auto h-8 w-8 animate-spin text-gray-500" />
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-gray-400">
                    No transactions yet
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.id} className="border-b border-gray-800/80 transition hover:bg-gray-900/50">
                    <td className="px-5 py-3.5 font-mono text-xs text-gray-400">{row.id}</td>
                    <td className="px-5 py-3.5">
                      <TypeBadge type={row.transaction_type} />
                    </td>
                    <td className="px-5 py-3.5 tabular-nums text-gray-50">{formatMoney(row.amount)}</td>
                    <td className="px-5 py-3.5 text-gray-300">{row.category}</td>
                    <td className="px-5 py-3.5 font-mono text-xs text-gray-400">{row.account_id}</td>
                    <td className="px-5 py-3.5 text-gray-400">{formatDate(row.created_at)}</td>
                    <td className="px-5 py-3.5 text-right">
                      {canTransfer ? (
                        <button
                          type="button"
                          title="Delete transaction"
                          disabled={deletingId === row.id}
                          onClick={() => handleDelete(row.id)}
                          className="inline-flex rounded-md p-1.5 text-gray-500 transition hover:bg-gray-800 hover:text-gray-300 disabled:opacity-40"
                          aria-label={`Delete transaction ${row.id}`}
                        >
                          {deletingId === row.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" strokeWidth={1.5} />
                          )}
                        </button>
                      ) : (
                        <span className="inline-block w-7" aria-hidden />
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-gray-800 px-5 py-4">
          <p className="text-xs text-gray-400">
            {total} record{total !== 1 ? 's' : ''} · Page {page} / {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={offset === 0 || loading}
              onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
              className="inline-flex items-center rounded border border-gray-700 px-3 py-1.5 text-xs text-gray-300 transition hover:bg-gray-800 disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              disabled={offset + PAGE_SIZE >= total || loading}
              onClick={() => setOffset((o) => o + PAGE_SIZE)}
              className="inline-flex items-center rounded border border-gray-700 px-3 py-1.5 text-xs text-gray-300 transition hover:bg-gray-800 disabled:opacity-40"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </GlassCard>

      <Modal open={modalOpen} title="New transfer" onClose={() => setModalOpen(false)}>
        <form onSubmit={submitTransfer} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">From account</label>
            <select
              required
              value={fromId}
              onChange={(e) => setFromId(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-[#0a0a0a] py-2.5 px-3 text-sm text-gray-50 focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            >
              <option value="">Select account</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  #{a.id} {a.name} ({formatMoney(a.balance)})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">To account</label>
            <select
              required
              value={toId}
              onChange={(e) => setToId(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-[#0a0a0a] py-2.5 px-3 text-sm text-gray-50 focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            >
              <option value="">Select account</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  #{a.id} {a.name} ({formatMoney(a.balance)})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">Amount</label>
            <input
              required
              type="text"
              inputMode="decimal"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-[#0a0a0a] py-2.5 px-3 text-sm text-gray-50 focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-400">Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-[#0a0a0a] py-2.5 px-3 text-sm text-gray-50 focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>
          {formError ? (
            <p className="rounded border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-300">{formError}</p>
          ) : null}
          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-600 bg-gray-800 py-2.5 text-sm font-medium text-gray-50 hover:bg-gray-700 disabled:opacity-50"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Submit transfer
          </button>
        </form>
      </Modal>
    </div>
  );
}
