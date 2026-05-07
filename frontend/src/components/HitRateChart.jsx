import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  CartesianGrid, ResponsiveContainer, LineChart, Line
} from 'recharts';
import { api } from '../api';

const CARD = {
  background: '#fff',
  borderRadius: '12px',
  padding: '20px 24px',
  boxShadow: '0 1px 4px rgba(0,0,0,0.10)',
  marginBottom: '24px',
};

export default function HitRateChart({ windowDays }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api.getHitRateByMonth(windowDays)
      .then(r => setData(r.data.data || []))
      .catch(e => setError(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, [windowDays]);

  if (loading) return <div style={{ color: '#888' }}>Loading chart…</div>;
  if (error) return (
    <div style={CARD}>
      <h3 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 600 }}>
        Hit Rate by Month ({windowDays}d window)
      </h3>
      <p style={{
        color: '#991b1b', background: '#fef2f2', border: '1px solid #fecaca',
        borderRadius: '8px', padding: '10px 14px', fontSize: '13px',
      }}>
        ❌ Could not load chart data: {error}
      </p>
    </div>
  );

  const chartData = data.map(d => ({
    month: d.month,
    Good: d.good,
    Bad: d.bad,
    Neutral: d.neutral,
    'Hit Rate %': +(d.hit_rate * 100).toFixed(1),
  }));

  return (
    <div style={CARD}>
      <h3 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 600 }}>
        Hit Rate by Month ({windowDays}d window)
      </h3>
      {chartData.length === 0 ? (
        <p style={{ color: '#888' }}>No data yet. Run ingestion first.</p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="right" orientation="right" unit="%" tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="Good" stackId="a" fill="#22c55e" />
              <Bar yAxisId="left" dataKey="Neutral" stackId="a" fill="#f59e0b" />
              <Bar yAxisId="left" dataKey="Bad" stackId="a" fill="#ef4444" />
              <Line yAxisId="right" type="monotone" dataKey="Hit Rate %" stroke="#0ea5e9" strokeWidth={2} dot />
            </BarChart>
          </ResponsiveContainer>
        </>
      )}
    </div>
  );
}
