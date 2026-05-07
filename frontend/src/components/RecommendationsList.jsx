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
  textAlign: 'left', padding: '8px 12px', background: '#f8fafc',
  borderBottom: '1px solid #e2e8f0', fontWeight: 600, color: '#374151',
};
const TD = { padding: '8px 12px', borderBottom: '1px solid #f1f5f9' };

function Badge({ label }) {
  const colors = {
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

const INPUT_STYLE = {
  padding: '6px 10px', borderRadius: '6px', border: '1px solid #d1d5db',
  fontSize: '13px', marginRight: '8px', marginBottom: '8px',
};

const BTN = {
  padding: '6px 14px', borderRadius: '6px', border: 'none', cursor: 'pointer',
  fontSize: '13px', fontWeight: 600, marginRight: '8px',
};

export default function RecommendationsList() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const [filters, setFilters] = useState({
    ticker: '', action: '', horizon_unit: '',
    date_from: '', date_to: '', window_days: 90,
  });

  const load = (p = page) => {
    setLoading(true);
    const params = { page: p, page_size: 15, ...filters };
    // Remove empty strings
    Object.keys(params).forEach(k => { if (params[k] === '') delete params[k]; });
    api.getRecommendations(params)
      .then(r => {
        setItems(r.data.items || []);
        setTotal(r.data.total || 0);
        setPage(p);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(1); }, []); // eslint-disable-line

  const handleFilter = () => load(1);

  const totalPages = Math.ceil(total / 15);

  return (
    <div style={CARD}>
      <h3 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 600 }}>
        📋 All Recommendations
      </h3>

      {/* Filters */}
      <div style={{ marginBottom: '16px' }}>
        <input style={INPUT_STYLE} placeholder="Ticker" value={filters.ticker}
          onChange={e => setFilters(f => ({ ...f, ticker: e.target.value }))} />
        <select style={INPUT_STYLE} value={filters.action}
          onChange={e => setFilters(f => ({ ...f, action: e.target.value }))}>
          <option value="">All Actions</option>
          <option value="buy">Buy</option>
          <option value="sell">Sell</option>
          <option value="hold">Hold</option>
          <option value="avoid">Avoid</option>
        </select>
        <select style={INPUT_STYLE} value={filters.horizon_unit}
          onChange={e => setFilters(f => ({ ...f, horizon_unit: e.target.value }))}>
          <option value="">All Horizons</option>
          <option value="day">Day</option>
          <option value="week">Week</option>
          <option value="month">Month</option>
          <option value="year">Year</option>
        </select>
        <input type="date" style={INPUT_STYLE} value={filters.date_from}
          onChange={e => setFilters(f => ({ ...f, date_from: e.target.value }))} />
        <input type="date" style={INPUT_STYLE} value={filters.date_to}
          onChange={e => setFilters(f => ({ ...f, date_to: e.target.value }))} />
        <button style={{ ...BTN, background: '#6366f1', color: '#fff' }} onClick={handleFilter}>
          Filter
        </button>
        <button style={{ ...BTN, background: '#f1f5f9', color: '#374151' }}
          onClick={() => { setFilters({ ticker: '', action: '', horizon_unit: '', date_from: '', date_to: '', window_days: 90 }); }}>
          Clear
        </button>
      </div>

      {loading ? (
        <p style={{ color: '#888' }}>Loading…</p>
      ) : items.length === 0 ? (
        <p style={{ color: '#888' }}>No recommendations found.</p>
      ) : (
        <>
          <p style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
            Showing {items.length} of {total} total
          </p>
          <table style={TABLE}>
            <thead>
              <tr>
                <th style={TH}>Ticker</th>
                <th style={TH}>Action</th>
                <th style={TH}>Entry Date</th>
                <th style={TH}>Mention Price</th>
                <th style={TH}>Target</th>
                <th style={TH}>Horizon</th>
                <th style={TH}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {items.map(r => (
                <tr key={r.id}>
                  <td style={{ ...TD, fontWeight: 600 }}>{r.resolved_ticker || r.raw_ticker}</td>
                  <td style={TD}><Badge label={r.action} /></td>
                  <td style={TD}>{r.entry_date}</td>
                  <td style={TD}>{r.mention_price ? `₹${r.mention_price.toLocaleString()}` : '—'}</td>
                  <td style={TD}>{r.target_price ? `₹${r.target_price.toLocaleString()}` : '—'}</td>
                  <td style={TD}>
                    {r.horizon_value ? `${r.horizon_value} ${r.horizon_unit}` : '—'}
                  </td>
                  <td style={TD}>{(r.confidence * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          {totalPages > 1 && (
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px', alignItems: 'center' }}>
              <button style={{ ...BTN, background: '#f1f5f9' }}
                disabled={page <= 1} onClick={() => load(page - 1)}>← Prev</button>
              <span style={{ fontSize: '13px' }}>Page {page} of {totalPages}</span>
              <button style={{ ...BTN, background: '#f1f5f9' }}
                disabled={page >= totalPages} onClick={() => load(page + 1)}>Next →</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
