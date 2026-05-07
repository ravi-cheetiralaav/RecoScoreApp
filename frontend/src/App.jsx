import { useState, useCallback } from 'react';
import SummaryCards from './components/SummaryCards';
import HitRateChart from './components/HitRateChart';
import TopWorstTables from './components/TopWorstTables';
import RecommendationsList from './components/RecommendationsList';
import IngestionPanel from './components/IngestionPanel';

const TABS = ['Dashboard', 'Recommendations'];

const WINDOW_OPTIONS = [30, 90, 180, 365];

function App() {
  const [tab, setTab] = useState('Dashboard');
  const [windowDays, setWindowDays] = useState(90);
  const [refreshKey, setRefreshKey] = useState(0);

  const onRefresh = useCallback(() => setRefreshKey(k => k + 1), []);

  return (
    <div style={{ minHeight: '100vh', background: '#f1f5f9', fontFamily: "'Inter', 'Segoe UI', sans-serif" }}>
      {/* Header */}
      <header style={{
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        color: '#fff', padding: '16px 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        boxShadow: '0 2px 8px rgba(99,102,241,0.3)',
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '22px', fontWeight: 800, letterSpacing: '-0.5px' }}>
            📈 RecoScoreApp
          </h1>
          <p style={{ margin: '2px 0 0', fontSize: '12px', opacity: 0.8 }}>
            Stock Recommendation Analyzer • Educational Use Only
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', opacity: 0.8 }}>Window:</span>
          {WINDOW_OPTIONS.map(w => (
            <button key={w}
              onClick={() => setWindowDays(w)}
              style={{
                padding: '4px 10px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                background: windowDays === w ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.1)',
                color: '#fff', fontWeight: windowDays === w ? 700 : 400, fontSize: '13px',
              }}>
              {w}d
            </button>
          ))}
        </div>
      </header>

      {/* Nav */}
      <nav style={{
        background: '#fff', borderBottom: '1px solid #e2e8f0',
        padding: '0 32px', display: 'flex', gap: '0',
      }}>
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '12px 20px', border: 'none', background: 'transparent',
            cursor: 'pointer', fontSize: '14px', fontWeight: tab === t ? 700 : 400,
            color: tab === t ? '#6366f1' : '#4b5563',
            borderBottom: tab === t ? '2px solid #6366f1' : '2px solid transparent',
          }}>
            {t}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 24px' }}>
        <IngestionPanel onRefresh={onRefresh} />

        {tab === 'Dashboard' && (
          <>
            <SummaryCards key={`summary-${refreshKey}`} windowDays={windowDays} />
            <HitRateChart key={`chart-${refreshKey}`} windowDays={windowDays} />
            <TopWorstTables key={`topworst-${refreshKey}`} windowDays={windowDays} />
          </>
        )}

        {tab === 'Recommendations' && (
          <RecommendationsList key={`recs-${refreshKey}`} />
        )}

        {/* Disclaimer */}
        <div style={{
          background: '#fffbeb', border: '1px solid #fde68a',
          borderRadius: '8px', padding: '12px 16px', marginTop: '24px',
          fontSize: '12px', color: '#78350f',
        }}>
          ⚠️ <strong>Disclaimer:</strong> This application is for educational analytics purposes only.
          It does not constitute investment advice. Past recommendation performance does not guarantee
          future results. Always consult a qualified financial advisor before making investment decisions.
        </div>
      </main>
    </div>
  );
}

export default App;
