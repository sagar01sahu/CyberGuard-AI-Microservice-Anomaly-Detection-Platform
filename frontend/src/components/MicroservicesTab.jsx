import React, { useState } from 'react';
import { ArrowRight, Network, Server, Cpu, Database, Eye, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function MicroservicesTab({ telemetryPackets }) {
  const [selectedPacket, setSelectedPacket] = useState(null);

  return (
    <div>
      {/* Visual Microservice Architecture Diagram */}
      <div className="glass-card flow-diagram-container">
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Network style={{ color: 'var(--accent-cyan)' }} /> Real-Time Microservice Inter-Process Data Pipeline
        </h3>

        <div className="service-pipeline">
          <div className="service-box active">
            <Server style={{ color: 'var(--accent-cyan)', marginBottom: '0.4rem' }} size={24} />
            <div className="service-title">Microservice 1</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Log Generator</div>
            <div className="service-tech">Python 3.10 / Faker</div>
          </div>

          <div className="pipeline-arrow">
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>POST /api/v1/logs/ingest</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
              <div className="flow-packet-dot"></div>
              <ArrowRight size={20} />
            </div>
            <span style={{ fontSize: '0.65rem', color: 'var(--accent-cyan)' }}>Header: X-API-Key</span>
          </div>

          <div className="service-box active">
            <Server style={{ color: 'var(--accent-purple)', marginBottom: '0.4rem' }} size={24} />
            <div className="service-title">Microservice 2</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Spring Boot Backend</div>
            <div className="service-tech">Java 17 / WebClient</div>
          </div>

          <div className="pipeline-arrow">
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>POST /predict</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
              <div className="flow-packet-dot" style={{ background: 'var(--accent-purple)', boxShadow: '0 0 10px var(--accent-purple)' }}></div>
              <ArrowRight size={20} />
            </div>
            <span style={{ fontSize: '0.65rem', color: 'var(--accent-purple)' }}>Current + 5 Historical Logs</span>
          </div>

          <div className="service-box active">
            <Cpu style={{ color: 'var(--accent-pink)', marginBottom: '0.4rem' }} size={24} />
            <div className="service-title">Microservice 3</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Python AI Engine</div>
            <div className="service-tech">FastAPI / PyTorch HGNN</div>
          </div>

          <div className="pipeline-arrow">
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Risk Score Output</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
              <ArrowRight size={20} />
            </div>
            <span style={{ fontSize: '0.65rem', color: 'var(--accent-pink)' }}>{`{ risk_score, explainability }`}</span>
          </div>

          <div className="service-box active">
            <Database style={{ color: 'var(--accent-emerald)', marginBottom: '0.4rem' }} size={24} />
            <div className="service-title">Storage & UI</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Postgres / React</div>
            <div className="service-tech">JPA / Vite UI</div>
          </div>
        </div>
      </div>

      {/* Live Data Transfer Table & Inspector Split View */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedPacket ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
        {/* Packets Stream Table */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Eye style={{ color: 'var(--accent-cyan)' }} /> Inter-Microservice Data Packets ({telemetryPackets.length})
          </h3>

          {telemetryPackets.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Waiting for microservice telemetry packets... Run the generator or trigger an attack!
            </div>
          ) : (
            <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Source &rarr; Target</th>
                    <th>Payload Type</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {telemetryPackets.map((pkt, idx) => (
                    <tr key={pkt.packetId || idx} style={{ background: selectedPacket?.packetId === pkt.packetId ? 'rgba(0,240,255,0.08)' : 'transparent' }}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                        {pkt.timestamp ? new Date(pkt.timestamp).toLocaleTimeString() : 'Just now'}
                      </td>
                      <td style={{ fontSize: '0.8rem' }}>
                        <div style={{ fontWeight: 600 }}>{pkt.sourceService?.split(':')[1] || pkt.sourceService}</div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>&rarr; {pkt.targetService?.split(':')[1] || pkt.targetService}</div>
                      </td>
                      <td style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                        {pkt.payloadType}
                      </td>
                      <td>
                        <span className={`status-pill ${pkt.status?.includes('ANOMALY') ? 'danger' : 'success'}`}>
                          {pkt.status?.includes('ANOMALY') ? <ShieldAlert size={10} /> : <CheckCircle2 size={10} />}
                          {pkt.status}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="btn-primary" 
                          style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                          onClick={() => setSelectedPacket(pkt)}
                        >
                          Inspect JSON
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Selected Packet JSON Inspector Modal / Panel */}
        {selectedPacket && (
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                Raw Microservice Data Payload Inspector
              </h3>
              <button 
                onClick={() => setSelectedPacket(null)} 
                style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: 700 }}
              >
                &times; Close
              </button>
            </div>

            <div style={{ marginBottom: '1rem', fontSize: '0.85rem' }}>
              <div><strong>Packet ID:</strong> <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-amber)' }}>{selectedPacket.packetId}</span></div>
              <div><strong>Route:</strong> {selectedPacket.sourceService} &rarr; {selectedPacket.targetService}</div>
              <div><strong>Endpoint:</strong> <span style={{ fontFamily: 'var(--font-mono)' }}>{selectedPacket.endpoint}</span></div>
              <div><strong>Protocol:</strong> {selectedPacket.protocol}</div>
              <div><strong>Latency:</strong> {selectedPacket.latencyMs ?? 0} ms</div>
            </div>

            <h4 style={{ fontSize: '0.85rem', marginBottom: '0.4rem', color: 'var(--text-secondary)' }}>Request Body Payload:</h4>
            <div className="json-box" style={{ marginBottom: '1rem' }}>
              {JSON.stringify(selectedPacket.requestBody, null, 2)}
            </div>

            <h4 style={{ fontSize: '0.85rem', marginBottom: '0.4rem', color: 'var(--text-secondary)' }}>Response Output Payload:</h4>
            <div className="json-box">
              {JSON.stringify(selectedPacket.responseBody, null, 2)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
