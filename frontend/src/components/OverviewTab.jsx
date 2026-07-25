import React, { useState } from 'react';
import { ShieldAlert, Activity, CheckCircle2, AlertTriangle, X, Terminal, Cpu, HardDrive, Globe, Lock, Shield, Layers } from 'lucide-react';

export default function OverviewTab({ stats, alerts, aiStatus }) {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'cards'

  const isTrained = aiStatus?.is_trained ?? false;

  const formatTimestamp = (ts) => {
    if (!ts) return 'N/A';
    try {
      const d = new Date(ts);
      return d.toISOString().substring(11, 19) + ' UTC';
    } catch {
      return String(ts);
    }
  };

  return (
    <div>
      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        <div className="glass-card kpi-card">
          <div>
            <div className="kpi-title">Total Ingested Logs</div>
            <div className="kpi-value">{stats?.totalLogsIngested ?? 0}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-cyan)', fontSize: '0.8rem', marginTop: '0.5rem' }}>
            <Activity size={14} /> Stream Active
          </div>
        </div>

        <div className="glass-card kpi-card">
          <div>
            <div className="kpi-title">Risk Alerts Triggered</div>
            <div className="kpi-value" style={{ color: (stats?.totalAlertsGenerated ?? 0) > 0 ? 'var(--accent-rose)' : 'var(--text-primary)' }}>
              {stats?.totalAlertsGenerated ?? 0}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-rose)', fontSize: '0.8rem', marginTop: '0.5rem' }}>
            <ShieldAlert size={14} /> Real-time Protection
          </div>
        </div>

        <div className="glass-card kpi-card">
          <div>
            <div className="kpi-title">AI HGNN Model Status</div>
            <div className="kpi-value" style={{ fontSize: '1.4rem' }}>
              {isTrained ? 'TRAINED' : 'UNTRAINED (INIT)'}
            </div>
          </div>
          <div style={{ marginTop: '0.5rem' }}>
            {isTrained ? (
              <span className="status-pill success"><CheckCircle2 size={12} /> GraphSAGE Ready</span>
            ) : (
              <span className="status-pill warning"><AlertTriangle size={12} /> Random Init Weights</span>
            )}
          </div>
        </div>

        <div className="glass-card kpi-card">
          <div>
            <div className="kpi-title">AI Predictions Served</div>
            <div className="kpi-value">{aiStatus?.total_predictions ?? 0}</div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Cold-Start: {aiStatus?.predictions_cold_start ?? 0} | HGNN: {aiStatus?.predictions_hgnn ?? 0}
          </div>
        </div>
      </div>

      {/* Live Alerts Table / Cards View */}
      <div className="glass-card" style={{ padding: '1.5rem', marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert style={{ color: 'var(--accent-rose)' }} /> Live Risk Alerts Stream
          </h3>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ background: '#080b11', padding: '0.2rem', borderRadius: '6px', border: '1px solid var(--border-color)', display: 'flex', gap: '0.2rem' }}>
              <button 
                onClick={() => setViewMode('table')}
                style={{
                  background: viewMode === 'table' ? 'var(--accent-blue)' : 'transparent',
                  color: viewMode === 'table' ? '#fff' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '0.3rem 0.6rem',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  fontWeight: 600
                }}
              >
                Table View
              </button>
              <button 
                onClick={() => setViewMode('cards')}
                style={{
                  background: viewMode === 'cards' ? 'var(--accent-blue)' : 'transparent',
                  color: viewMode === 'cards' ? '#fff' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '0.3rem 0.6rem',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  fontWeight: 600
                }}
              >
                Cards View
              </button>
            </div>
            <span className="status-pill success"><span className="pulse-dot"></span> Live Pipeline</span>
          </div>
        </div>

        {alerts.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No high-risk security threats detected yet. Trigger an attack scenario in the Attack Simulator tab!
          </div>
        ) : viewMode === 'table' ? (
          /* Table Layout matching Screenshot #3 */
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>ALERT ID</th>
                  <th style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>TIMESTAMP</th>
                  <th style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>ENTITY ID</th>
                  <th style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>SEVERITY</th>
                  <th style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>ANOMALY TYPE</th>
                  <th style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>RISK SCORE</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert, idx) => {
                  const id = alert.alertId ?? alert.alert_id ?? (idx + 1000);
                  const score = alert.riskScore ?? alert.risk_score ?? 0.0;
                  const type = alert.anomalyType ?? alert.anomaly_type ?? 'Anomaly';
                  const entity = alert.entityId ?? alert.entity_id ?? 'Unknown';
                  const ts = formatTimestamp(alert.timestamp);
                  const isCritical = alert.severity === 'CRITICAL';

                  return (
                    <tr 
                      key={id}
                      onClick={() => setSelectedAlert(alert)}
                      style={{ 
                        borderBottom: '1px solid rgba(255,255,255,0.03)',
                        cursor: 'pointer',
                        transition: 'background 0.15s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '0.85rem 1rem', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>#{id}</td>
                      <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>{ts}</td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <span style={{ background: 'rgba(0, 240, 255, 0.1)', color: 'var(--accent-cyan)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                          {entity}
                        </span>
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <span className={`status-pill ${isCritical ? 'danger' : 'warning'}`}>
                          <AlertTriangle size={12} /> {alert.severity || 'HIGH'}
                        </span>
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <span style={{ 
                          border: `1px solid ${type.includes('Cold') ? 'var(--accent-cyan)' : 'var(--accent-amber)'}`,
                          color: type.includes('Cold') ? 'var(--accent-cyan)' : 'var(--accent-amber)',
                          background: 'rgba(0,0,0,0.3)',
                          padding: '0.25rem 0.6rem',
                          borderRadius: '6px',
                          fontSize: '0.8rem',
                          fontWeight: 600
                        }}>
                          {type}
                        </span>
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden', minWidth: '80px' }}>
                            <div style={{ width: `${Math.min(100, score * 100)}%`, height: '100%', background: 'var(--gradient-danger)' }}></div>
                          </div>
                          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-rose)' }}>
                            {score.toFixed(2)}
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>
                        <button 
                          onClick={(e) => { e.stopPropagation(); setSelectedAlert(alert); }}
                          style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-blue)', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '0.3rem 0.7rem', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer', fontWeight: 600 }}
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          /* Cards View matching Screenshot #2 */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {alerts.map((alert, idx) => {
              const score = alert.riskScore ?? alert.risk_score ?? 0.0;
              const type = alert.anomalyType ?? alert.anomaly_type ?? 'Anomaly';
              const entity = alert.entityId ?? alert.entity_id ?? 'Unknown';
              const factors = alert.explainabilityFactors ?? alert.explainability_factors ?? [];
              const factorsStr = Array.isArray(factors) ? factors.join(', ') : String(factors || '');

              return (
                <div 
                  key={alert.alertId ?? alert.alert_id ?? idx}
                  onClick={() => setSelectedAlert(alert)}
                  style={{
                    background: 'rgba(18, 24, 36, 0.7)',
                    border: '1px solid var(--border-color)',
                    borderLeft: `4px solid ${
                      alert.severity === 'CRITICAL' ? 'var(--accent-rose)' :
                      alert.severity === 'HIGH' ? 'var(--accent-amber)' : 'var(--accent-blue)'
                    }`,
                    borderRadius: '10px',
                    padding: '1rem',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span className={`status-pill ${alert.severity === 'CRITICAL' || alert.severity === 'HIGH' ? 'danger' : 'warning'}`}>
                        {alert.severity}
                      </span>
                      <span style={{ fontWeight: 700, fontSize: '1rem' }}>{type}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>
                        {entity}
                      </span>
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-rose)' }}>
                      Risk Score: {(score * 100).toFixed(1)}%
                    </div>
                  </div>

                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', background: '#080b11', padding: '0.6rem 0.8rem', borderRadius: '6px', fontFamily: 'var(--font-sans)' }}>
                    <strong>Explainability:</strong> {factorsStr || 'N/A'}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Side Inspection Drawer Modal matching Screenshot #4 */}
      {selectedAlert && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(4px)',
          zIndex: 1000,
          display: 'flex',
          justifyContent: 'flex-end'
        }}>
          <div style={{
            width: '500px',
            maxWidth: '90vw',
            height: '100%',
            background: '#0c1017',
            borderLeft: '2px solid var(--accent-rose)',
            padding: '2rem',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem',
            boxShadow: '-10px 0 30px rgba(0,0,0,0.8)'
          }}>
            {/* Drawer Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    ALERT #{selectedAlert.alertId ?? selectedAlert.alert_id ?? '2031'}
                  </span>
                  <span className="status-pill danger" style={{ fontSize: '0.7rem' }}>
                    {selectedAlert.severity || 'CRITICAL'}
                  </span>
                </div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>
                  {selectedAlert.anomalyType ?? selectedAlert.anomaly_type ?? 'Lateral Movement'}
                </h2>
              </div>
              <button 
                onClick={() => setSelectedAlert(null)}
                style={{ background: 'rgba(255,255,255,0.05)', border: 'none', color: 'var(--text-secondary)', padding: '0.4rem', borderRadius: '6px', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* PyTorch Explainability Box */}
            <div style={{ background: 'rgba(244, 63, 94, 0.05)', border: '1px solid rgba(244, 63, 94, 0.2)', borderRadius: '10px', padding: '1.2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.5px', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Cpu size={14} /> PYTORCH HGNN EXPLAINABILITY
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-rose)' }}>
                  Risk Score: {(((selectedAlert.riskScore ?? selectedAlert.risk_score ?? 0.96) * 100)).toFixed(0)}%
                </span>
              </div>
              <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'var(--text-primary)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {Array.isArray(selectedAlert.explainabilityFactors ?? selectedAlert.explainability_factors) ? (
                  (selectedAlert.explainabilityFactors ?? selectedAlert.explainability_factors).map((f, i) => <li key={i}>{f}</li>)
                ) : (
                  <li>{selectedAlert.explainabilityFactors ?? selectedAlert.explainability_factors ?? 'Anomaly detected via graph embedding distance.'}</li>
                )}
              </ul>
            </div>

            {/* Context Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div style={{ background: 'rgba(18, 24, 36, 0.8)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <Shield size={12} /> ENTITY ID
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--accent-cyan)', fontWeight: 700 }}>
                  {selectedAlert.entityId ?? selectedAlert.entity_id ?? 'user_0377'}
                </div>
              </div>

              <div style={{ background: 'rgba(18, 24, 36, 0.8)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <Globe size={12} /> SOURCE IP
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: '#fff', fontWeight: 600 }}>
                  {selectedAlert.sourceIp ?? selectedAlert.source_ip ?? '192.168.4.12'}
                </div>
              </div>

              <div style={{ background: 'rgba(18, 24, 36, 0.8)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <HardDrive size={12} /> DEVICE ID
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-primary)', wordBreak: 'break-all' }}>
                  {selectedAlert.deviceId ?? selectedAlert.device_id ?? 'macbook_pro_m2_xyz'}
                </div>
              </div>

              <div style={{ background: 'rgba(18, 24, 36, 0.8)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <Lock size={12} /> RESOURCE TARGET
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--accent-amber)', wordBreak: 'break-all' }}>
                  {selectedAlert.resourceAccessed ?? selectedAlert.resource_accessed ?? '/api/v1/finance/payroll_2026.csv'}
                </div>
              </div>
            </div>

            {/* Feature Vectors Box */}
            <div style={{ background: 'rgba(18, 24, 36, 0.8)', padding: '1.2rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.8rem', letterSpacing: '0.5px' }}>
                GRAPH NEURAL NETWORK FEATURE VECTORS
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>User Embedding Cosine Distance:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-rose)', fontWeight: 700 }}>0.892 (Threshold 0.85)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>FedAvg Peer Consensus Std Dev:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-amber)', fontWeight: 700 }}>3.82 σ</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Inference Execution Latency:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-emerald)', fontWeight: 700 }}>14.2 ms</span>
                </div>
              </div>
            </div>

            {/* Recommended SOC Actions */}
            <div style={{ marginTop: 'auto' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.8rem', letterSpacing: '0.5px' }}>
                RECOMMENDED SOC ACTION
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.6rem' }}>
                <button 
                  onClick={() => alert(`Quarantined ${selectedAlert.entityId ?? selectedAlert.entity_id}`)}
                  style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.4)', color: 'var(--accent-amber)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem' }}
                >
                  <Lock size={14} /> Quarantine
                </button>
                <button 
                  onClick={() => alert(`Blocked IP ${selectedAlert.sourceIp ?? selectedAlert.source_ip}`)}
                  style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.4)', color: 'var(--accent-rose)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem' }}
                >
                  <ShieldAlert size={14} /> Block IP
                </button>
                <button 
                  onClick={() => setSelectedAlert(null)}
                  style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem' }}
                >
                  <CheckCircle2 size={14} /> Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

