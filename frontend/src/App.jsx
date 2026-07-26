import React, { useState, useEffect, useRef } from 'react';
import { ShieldAlert, Network, Cpu, Flame, LayoutDashboard, RefreshCw } from 'lucide-react';
import OverviewTab from './components/OverviewTab';
import MicroservicesTab from './components/MicroservicesTab';
import AiEngineTab from './components/AiEngineTab';
import AttackSimulatorTab from './components/AttackSimulatorTab';

const SPRING_BOOT_BASE = 'http://localhost:8080/api/v1';
const AI_ENGINE_BASE = 'http://localhost:8000';
const GENERATOR_CONTROL_BASE = 'http://localhost:8001/api/v1/generator';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [telemetry, setTelemetry] = useState([]);
  const [logs, setLogs] = useState([]);
  const [aiStatus, setAiStatus] = useState(null);
  const [loading, setLoading] = useState(true);


  const jwtToken = useRef(null);

  const fetchAllData = async () => {
    try {

      if (!jwtToken.current) {
        const tokenRes = await fetch(`${SPRING_BOOT_BASE}/auth/dev-token?subject=analyst`, {
          method: 'POST'
        });

        if (tokenRes.ok) {
          const tokenData = await tokenRes.json();
          jwtToken.current = tokenData.token;
        } else {
          console.error('Failed to fetch JWT token. Ensure Spring Boot is running with the "dev" profile.');
          return;
        }
      }


      const authHeaders = {
        'Authorization': `Bearer ${jwtToken.current}`,
        'Content-Type': 'application/json'
      };


      const statsRes = await fetch(`${SPRING_BOOT_BASE}/dashboard/stats`, { headers: authHeaders })
          .then(r => r.ok ? r.json() : null).catch(() => null);
      const alertsRes = await fetch(`${SPRING_BOOT_BASE}/alerts/live`, { headers: authHeaders })
          .then(r => r.ok ? r.json() : []).catch(() => []);
      const telemetryRes = await fetch(`${SPRING_BOOT_BASE}/dashboard/telemetry`, { headers: authHeaders })
          .then(r => r.ok ? r.json() : []).catch(() => []);
      const logsRes = await fetch(`${SPRING_BOOT_BASE}/dashboard/logs`, { headers: authHeaders })
          .then(r => r.ok ? r.json() : []).catch(() => []);

      if (statsRes) setStats(statsRes);
      if (alertsRes) setAlerts(alertsRes);
      if (telemetryRes) setTelemetry(telemetryRes);
      if (logsRes) setLogs(logsRes);


      const aiRes = await fetch(`${AI_ENGINE_BASE}/model/status`)
          .then(r => r.ok ? r.json() : null).catch(() => null);
      if (aiRes) setAiStatus(aiRes);

    } catch (err) {
      console.warn('Polling error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleTrainModel = async () => {
    const res = await fetch(`${AI_ENGINE_BASE}/model/train?epochs=20`, { method: 'POST' });
    const json = await res.json();
    await fetchAllData();
    return json;
  };

  const handleTriggerAttack = async (attackType) => {
    const res = await fetch(`${GENERATOR_CONTROL_BASE}/inject-attack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ attack_type: attackType, target_role: 'MARKETING' }),
    });
    const json = await res.json();
    await fetchAllData();
    return json;
  };

  return (
      <div>

        <nav className="navbar">
          <div className="logo-container">
            <div className="logo-icon">
              <ShieldAlert size={22} />
            </div>
            <div>
              <div className="logo-text">CyberGuard AI</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>
                MICROSERVICE ANOMALY DETECTION ENGINE
              </div>
            </div>
          </div>


          <div className="nav-tabs">
            <button
                className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
            >
              <LayoutDashboard size={16} /> Overview
            </button>
            <button
                className={`tab-btn ${activeTab === 'microservices' ? 'active' : ''}`}
                onClick={() => setActiveTab('microservices')}
            >
              <Network size={16} /> Microservice Flow & Data Inspector
            </button>
            <button
                className={`tab-btn ${activeTab === 'ai-engine' ? 'active' : ''}`}
                onClick={() => setActiveTab('ai-engine')}
            >
              <Cpu size={16} /> AI Engine (HGNN)
            </button>
            <button
                className={`tab-btn ${activeTab === 'attacks' ? 'active' : ''}`}
                onClick={() => setActiveTab('attacks')}
            >
              <Flame size={16} /> Attack Simulator
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
                onClick={fetchAllData}
                style={{ background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', padding: '0.4rem 0.8rem', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem' }}
            >
              <RefreshCw size={12} /> Sync
            </button>
            <span className="status-pill success">
            <span className="pulse-dot"></span> System Live
          </span>
          </div>
        </nav>


        <main className="app-container">
          {activeTab === 'overview' && (
              <OverviewTab stats={stats} alerts={alerts} aiStatus={aiStatus} />
          )}
          {activeTab === 'microservices' && (
              <MicroservicesTab telemetryPackets={telemetry} />
          )}
          {activeTab === 'ai-engine' && (
              <AiEngineTab aiStatus={aiStatus} onTrainModel={handleTrainModel} />
          )}
          {activeTab === 'attacks' && (
              <AttackSimulatorTab logs={logs} onTriggerAttack={handleTriggerAttack} />
          )}
        </main>
      </div>
  );
}