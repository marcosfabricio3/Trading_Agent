import React, { useEffect, useState } from 'react';
import { Activity, TrendingUp, Shield, BarChart3, CloudLightning, RefreshCw } from 'lucide-react';

interface Trade {
  id: number;
  symbol: string;
  side: string;
  entry_price: number;
  tp: number;
  sl: number;
  tp1_hit: number; // SQLite returns 0/1
}

const App = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [balance, setBalance] = useState(0);
  const [lastUpdate, setLastUpdate] = useState(new Date().toLocaleTimeString());

  const fetchData = async () => {
    try {
      const tResponse = await fetch('http://localhost:8000/api/trades');
      const tData = await tResponse.json();
      setTrades(tData.active || []);

      const bResponse = await fetch('http://localhost:8000/api/balance');
      const bData = await bResponse.json();
      setBalance(bData.balance || 0);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (e) {
      console.error("API Error:", e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-container">
      <header>
        <div className="logo">
          <Shield size={24} style={{ filter: 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.5))' }} />
          TRADING AGENT PRO
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', color: '#94A3B8', fontSize: '0.875rem' }}>
          <div className="pulse-icon"></div>
          ACTIVE MONITORING
        </div>
      </header>

      <style>{`
        .pulse-icon {
          width: 8px;
          height: 8px;
          background: #10B981;
          border-radius: 50%;
          box-shadow: 0 0 0 rgba(16, 185, 129, 0.4);
          animation: pulse 2s infinite;
        }
        @keyframes pulse {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
          70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
      `}</style>

      <div className="stat-grid">
        <div className="card">
          <h3>EQUITY (USDT)</h3>
          <div className="value">${balance.toLocaleString()}</div>
        </div>
        <div className="card">
          <h3>OPEN POSITIONS</h3>
          <div className="value">{trades.length}</div>
        </div>
        <div className="card">
          <h3>DAILY PnL</h3>
          <div className="value pnl-plus">+$0.00</div>
        </div>
        <div className="card">
          <h3>WIN RATE</h3>
          <div className="value">0%</div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem' }}>Active Positions</h2>
        <div style={{ fontSize: '0.75rem', color: '#64748B', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <RefreshCw size={12} />
          Last update: {lastUpdate}
        </div>
      </div>
      
      <div className="trade-list">
        <div className="trade-row trade-header">
          <div>ASSET / SIDE</div>
          <div className="hide-mobile">ENTRY</div>
          <div className="hide-mobile">TARGET (TP1)</div>
          <div>PnL %</div>
          <div>STATUS</div>
        </div>
        
        {trades.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748B' }}>
            <BarChart3 size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
            <p>No active positions detected</p>
          </div>
        ) : (
          trades.map(trade => (
            <div key={trade.id} className="trade-row">
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <CloudLightning size={20} color="#3B82F6" />
                <div>
                  <div style={{ fontWeight: 600 }}>{trade.symbol}</div>
                  <div className={`badge ${trade.side.toLowerCase() === 'long' ? 'badge-long' : 'badge-short'}`}>
                    {trade.side.toUpperCase()}
                  </div>
                </div>
              </div>
              <div className="hide-mobile">${trade.entry_price}</div>
              <div className="hide-mobile">${trade.tp}</div>
              <div className="pnl-plus">+0.00%</div>
              <div style={{ color: trade.tp1_hit === 1 ? '#10B981' : '#94A3B8' }}>
                {trade.tp1_hit === 1 ? 'TP1 HIT ✓' : 'WATCHING'}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default App;
