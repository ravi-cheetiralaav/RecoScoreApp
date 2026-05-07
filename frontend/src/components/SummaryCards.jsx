import { useState, useEffect } from 'react';
import { api } from '../api';

const CARD_STYLE = {
  background: '#fff',
  borderRadius: '12px',
  padding: '20px 24px',
  boxShadow: '0 1px 4px rgba(0,0,0,0.10)',
  flex: '1 1 160px',
  minWidth: 0,
};

const METRIC_ROW = {
  display: 'flex',
  gap: '16px',
  flexWrap: 'wrap',
  marginBottom: '24px',
};

export default function SummaryCards({ windowDays }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getSummary(windowDays)
      .then(r => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [windowDays]);

  if (loading) return <div style={{ color: '#888', marginBottom: '24px' }}>Loading metrics…</div>;
  if (!data) return null;

  const hitPct = (data.hit_rate * 100).toFixed(1);

  return (
    <div style={METRIC_ROW}>
      <div style={CARD_STYLE}>
        <div style={{ fontSize: '13px', color: '#666', marginBottom: '6px' }}>Total Recommendations</div>
        <div style={{ fontSize: '32px', fontWeight: 700 }}>{data.total_recommendations}</div>
      </div>
      <div style={{ ...CARD_STYLE, borderTop: '3px solid #22c55e' }}>
        <div style={{ fontSize: '13px', color: '#666', marginBottom: '6px' }}>Good ✅</div>
        <div style={{ fontSize: '32px', fontWeight: 700, color: '#16a34a' }}>{data.good}</div>
      </div>
      <div style={{ ...CARD_STYLE, borderTop: '3px solid #ef4444' }}>
        <div style={{ fontSize: '13px', color: '#666', marginBottom: '6px' }}>Bad ❌</div>
        <div style={{ fontSize: '32px', fontWeight: 700, color: '#dc2626' }}>{data.bad}</div>
      </div>
      <div style={{ ...CARD_STYLE, borderTop: '3px solid #f59e0b' }}>
        <div style={{ fontSize: '13px', color: '#666', marginBottom: '6px' }}>Neutral ➖</div>
        <div style={{ fontSize: '32px', fontWeight: 700, color: '#d97706' }}>{data.neutral}</div>
      </div>
      <div style={{ ...CARD_STYLE, borderTop: '3px solid #6366f1' }}>
        <div style={{ fontSize: '13px', color: '#666', marginBottom: '6px' }}>Pending ⏳</div>
        <div style={{ fontSize: '32px', fontWeight: 700, color: '#4f46e5' }}>{data.pending}</div>
      </div>
      <div style={{ ...CARD_STYLE, borderTop: '3px solid #0ea5e9' }}>
        <div style={{ fontSize: '13px', color: '#666', marginBottom: '6px' }}>Hit Rate ({windowDays}d)</div>
        <div style={{ fontSize: '32px', fontWeight: 700, color: '#0284c7' }}>{hitPct}%</div>
      </div>
      <div style={{ ...CARD_STYLE, borderTop: '3px solid #8b5cf6' }}>
        <div style={{ fontSize: '13px', color: '#666', marginBottom: '6px' }}>Avg Return</div>
        <div style={{
          fontSize: '32px', fontWeight: 700,
          color: data.avg_return_pct >= 0 ? '#16a34a' : '#dc2626',
        }}>
          {data.avg_return_pct >= 0 ? '+' : ''}{data.avg_return_pct.toFixed(1)}%
        </div>
      </div>
    </div>
  );
}
