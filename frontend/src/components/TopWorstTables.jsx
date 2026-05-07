import { useState, useEffect } from 'react';
import { api } from '../api';

const CARD = {
  background: '#fff',
  borderRadius: '12px',
  padding: '20px 24px',
  boxShadow: '0 1px 4px rgba(0,0,0,0.10)',
  marginBottom: '24px',
};

const TABLE = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: '13px',
};

const TH = {
  textAlign: 'left',
  padding: '8px 12px',
  background: '#f8fafc',
  borderBottom: '1px solid #e2e8f0',
  fontWeight: 600,
  color: '#374151',
};

const TD = { padding: '8px 12px', borderBottom: '1px solid #f1f5f9' };

function Badge({ label }) {
  const colors = {
    good: { bg: '#dcfce7', text: '#16a34a' },
    bad: { bg: '#fee2e2', text: '#dc2626' },
    neutral: { bg: '#fef3c7', text: '#d97706' },
    pending: { bg: '#e0e7ff', text: '#4338ca' },
    buy: { bg: '#dbeafe', text: '#1d4ed8' },
    sell: { bg: '#fee2e2', text: '#dc2626' },
    hold: { bg: '#fef3c7', text: '#d97706' },
    avoid: { bg: '#fce7f3', text: '#9d174d' },
  };
  const c = colors[label?.toLowerCase()] || { bg: '#f1f5f9', text: '#374151' };
  return (
    <span style={{
      background: c.bg, color: c.text,
      padding: '2px 8px', borderRadius: '9999px',
      fontSize: '11px', fontWeight: 600,
    }}>
      {label}
    </span>
  );
}

function RecoTable({ rows, emptyMsg }) {
  if (!rows || rows.length === 0) return <p style={{ color: '#888' }}>{emptyMsg}</p>;
  return (
    <table style={TABLE}>
      <thead>
        <tr>
          <th style={TH}>Ticker</th>
          <th style={TH}>Action</th>
          <th style={TH}>Entry Date</th>
          <th style={TH}>Entry Price</th>
          <th style={TH}>Exit Price</th>
          <th style={TH}>Return</th>
          <th style={TH}>Result</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(r => (
          <tr key={r.recommendation_id}>
            <td style={{ ...TD, fontWeight: 600 }}>{r.ticker}</td>
            <td style={TD}><Badge label={r.action} /></td>
            <td style={TD}>{r.entry_date}</td>
            <td style={TD}>{r.entry_price ? `₹${r.entry_price.toLocaleString()}` : '—'}</td>
            <td style={TD}>{r.exit_price ? `₹${r.exit_price.toLocaleString()}` : '—'}</td>
            <td style={{
              ...TD, fontWeight: 600,
              color: r.return_pct > 0 ? '#16a34a' : r.return_pct < 0 ? '#dc2626' : '#374151',
            }}>
              {r.return_pct != null ? `${r.return_pct > 0 ? '+' : ''}${r.return_pct.toFixed(1)}%` : '—'}
            </td>
            <td style={TD}><Badge label={r.classification} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function TopWorstTables({ windowDays }) {
  const [top, setTop] = useState([]);
  const [worst, setWorst] = useState([]);

  useEffect(() => {
    api.getTopRecommendations(5, windowDays).then(r => setTop(r.data.data || [])).catch(console.error);
    api.getWorstRecommendations(5, windowDays).then(r => setWorst(r.data.data || [])).catch(console.error);
  }, [windowDays]);

  return (
    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
      <div style={{ ...CARD, flex: '1 1 400px', minWidth: 0 }}>
        <h3 style={{ margin: '0 0 12px', fontSize: '15px', fontWeight: 600 }}>🏆 Top Calls</h3>
        <RecoTable rows={top} emptyMsg="No scored recommendations yet." />
      </div>
      <div style={{ ...CARD, flex: '1 1 400px', minWidth: 0 }}>
        <h3 style={{ margin: '0 0 12px', fontSize: '15px', fontWeight: 600 }}>📉 Worst Calls</h3>
        <RecoTable rows={worst} emptyMsg="No scored recommendations yet." />
      </div>
    </div>
  );
}
