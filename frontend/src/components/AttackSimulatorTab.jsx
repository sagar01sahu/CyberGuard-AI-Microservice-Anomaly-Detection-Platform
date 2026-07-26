import React, { useState } from 'react';
import { Flame, ShieldAlert, Zap, Globe, Lock, Smartphone, RefreshCw } from 'lucide-react';

export default function AttackSimulatorTab({ logs, onTriggerAttack }) {
  const [triggering, setTriggering] = useState(null);
  const [lastResult, setLastResult] = useState(null);

  const attacks = [
    { id: 'brute_force', name: 'Brute Force Attack', icon: Lock, color: 'var(--accent-amber)', desc: 'Generate multiple failed login attempts followed by success' },
    { id: 'impossible_travel', name: 'Impossible Travel', icon: Globe, color: 'var(--accent-cyan)', desc: 'Two consecutive logins from India and Germany within minutes' },
    { id: 'lateral_movement', name: 'Lateral Movement', icon: Zap, color: 'var(--accent-pink)', desc: 'Marketing user attempting unauthorized access to payroll/finance' },
    { id: 'device_spoofing', name: 'Device Spoofing', icon: Smartphone, color: 'var(--accent-purple)', desc: 'Sudden OS and device fingerprint change mid-session' },
  ];

  const handleInject = async (attackId) => {
    setTriggering(attackId);
    setLastResult(null);
    try {
      const res = await onTriggerAttack(attackId);
      setLastResult(res);
    } catch (e) {
      setLastResult({ error: e.message });
    } finally {
      setTriggering(null);
    }
  };

  return (
    <div>

      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 800, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Flame style={{ color: 'var(--accent-rose)' }} /> On-Demand Cyber Attack Injector
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Click an attack scenario below to inject malicious log events into the synthetic log generator stream and observe how the Spring Boot Backend and HGNN AI Engine detect them in real time!
        </p>

        <div className="kpi-grid">
          {attacks.map((atk) => {
            const Icon = atk.icon;
            const isRunning = triggering === atk.id;
            return (
              <div 
                key={atk.id} 
                className="glass-card" 
                style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', background: 'rgba(18,24,36,0.8)' }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Icon size={20} style={{ color: atk.color }} />
                    <strong style={{ fontSize: '1rem', color: '#fff' }}>{atk.name}</strong>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    {atk.desc}
                  </p>
                </div>

                <button 
                  className="btn-danger" 
                  onClick={() => handleInject(atk.id)}
                  disabled={isRunning}
                  style={{ width: '100%', justifyContent: 'center' }}
                >
                  {isRunning ? <RefreshCw className="animate-spin" size={14} /> : <ShieldAlert size={14} />}
                  {isRunning ? 'Injecting Attack...' : 'Inject Attack Scenario'}
                </button>
              </div>
            );
          })}
        </div>


        {lastResult && (
          <div style={{ marginTop: '1.5rem', background: '#080b11', border: '1px solid var(--border-glow)', padding: '1rem', borderRadius: '8px' }}>
            <h4 style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', marginBottom: '0.4rem' }}>Attack Injection Status:</h4>
            <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
              {JSON.stringify(lastResult, null, 2)}
            </pre>
          </div>
        )}
      </div>


      <div className="glass-card" style={{ padding: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
          Live Access Log Stream ({logs.length} events)
        </h3>

        {logs.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No access logs ingested yet. Start the system launcher!
          </div>
        ) : (
          <div style={{ maxHeight: '450px', overflowY: 'auto' }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Entity ID</th>
                  <th>Resource Accessed</th>
                  <th>Source IP</th>
                  <th>Device / OS</th>
                  <th>Auth Status</th>
                  <th>AI Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id || Math.random()}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                      {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'N/A'}
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{log.entityId}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{log.resourceAccessed}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{log.sourceIp}</td>
                    <td style={{ fontSize: '0.8rem' }}>{log.deviceId} ({log.osVersion})</td>
                    <td>
                      <span className={`status-pill ${log.authStatus === 'SUCCESS' ? 'success' : 'danger'}`}>
                        {log.authStatus}
                      </span>
                    </td>
                    <td>
                      <span className={`status-pill ${log.processingStatus === 'ANALYZED' ? 'success' : 'warning'}`}>
                        {log.processingStatus}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
