import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import api from '../services/api';
import { formatDate } from '../utils/format';

export default function Audit() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get('/audit/', { params: { offset: 0, limit: 100 } });
        if (!cancelled && data?.success && data.data) {
          setItems(data.data.items ?? []);
          setTotal(data.data.total ?? 0);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-gray-50">Audit logs</h1>
        <p className="mt-1 text-sm text-gray-400">Immutable system trail ({total} events)</p>
      </header>

      <div className="overflow-hidden rounded-xl border border-gray-800 bg-[#111111]">
        <div className="border-b border-gray-800 bg-gray-950 px-4 py-2 font-mono text-[10px] uppercase tracking-widest text-gray-500">
          zorvyn-audit :: readonly
        </div>
        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          </div>
        ) : (
          <div className="max-h-[70vh] overflow-auto">
            <table className="w-full font-mono text-xs">
              <thead className="sticky top-0 z-10 bg-[#111111] text-left text-gray-400">
                <tr>
                  <th className="px-4 py-2 font-medium">ts</th>
                  <th className="px-4 py-2 font-medium">action</th>
                  <th className="px-4 py-2 font-medium">table</th>
                  <th className="px-4 py-2 font-medium">record</th>
                  <th className="px-4 py-2 font-medium">user</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-12 text-center text-gray-500">
                      No audit entries
                    </td>
                  </tr>
                ) : (
                  items.map((log) => (
                    <tr key={log.id} className="terminal-row hover:bg-gray-900/80">
                      <td className="whitespace-nowrap px-4 py-2 text-gray-400">{formatDate(log.timestamp)}</td>
                      <td className="px-4 py-2 text-gray-200">{log.action}</td>
                      <td className="px-4 py-2 text-gray-400">{log.table_name}</td>
                      <td className="px-4 py-2 text-gray-300">{log.record_id ?? '—'}</td>
                      <td className="px-4 py-2 text-gray-500">{log.user_id ?? '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
