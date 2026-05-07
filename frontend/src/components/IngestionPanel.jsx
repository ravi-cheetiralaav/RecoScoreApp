import { useState } from 'react';
import { api } from '../api';

const BTN = {
  padding: '8px 18px', borderRadius: '8px', border: 'none',
  cursor: 'pointer', fontWeight: 600, fontSize: '14px',
};

export default function IngestionPanel({ onRefresh }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(20);

  const trigger = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.triggerIngestion(limit);
      setResult(r.data);
      if (onRefresh) onRefresh();
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  const recompute = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.recomputeScores();
      if (onRefresh) onRefresh();
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      background: '#fff', borderRadius: '12px', padding: '20px 24px',
      boxShadow: '0 1px 4px rgba(0,0,0,0.10)', marginBottom: '24px',
    }}>
      <h3 style={{ margin: '0 0 12px', fontSize: '16px', fontWeight: 600 }}>⚡ Pipeline Controls</h3>
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
        <label style={{ fontSize: '13px' }}>
          Posts limit:{' '}
          <input
            type="number" min="1" max="50" value={limit}
            onChange={e => setLimit(+e.target.value)}
            style={{ width: '60px', padding: '4px 6px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '13px' }}
          />
        </label>
        <button
          style={{ ...BTN, background: loading ? '#94a3b8' : '#6366f1', color: '#fff' }}
          onClick={trigger} disabled={loading}
        >
          {loading ? 'Running…' : '🚀 Run Ingestion Pipeline'}
        </button>
        <button
          style={{ ...BTN, background: loading ? '#94a3b8' : '#0ea5e9', color: '#fff' }}
          onClick={recompute} disabled={loading}
        >
          🔄 Recompute Scores
        </button>
      </div>

      {result && (
        <div style={{
          marginTop: '12px', padding: '10px 14px', background: '#f0fdf4',
          borderRadius: '8px', fontSize: '13px', color: '#166534'
        }}>
          ✅ Fetched <b>{result.fetched}</b> posts | New: <b>{result.new}</b> |
          Processed: <b>{result.processed}</b> recs | Scored: <b>{result.scored}</b>
        </div>
      )}
      {error && (
        <div style={{
          marginTop: '12px', padding: '10px 14px', background: '#fef2f2',
          borderRadius: '8px', fontSize: '13px', color: '#991b1b'
        }}>
          ❌ Error: {error}
        </div>
      )}
    </div>
  );
}
