import React, { useState } from 'react';
import { Cpu, CheckCircle2, AlertTriangle, Play, RefreshCw, GitBranch, Layers } from 'lucide-react';

export default function AiEngineTab({ aiStatus, onTrainModel }) {
  const [isTraining, setIsTraining] = useState(false);
  const [trainLogs, setTrainLogs] = useState(null);

  const handleTrainClick = async () => {
    setIsTraining(true);
    setTrainLogs("Initializing self-supervised contrastive HGNN training...");
    try {
      const res = await onTrainModel();
      setTrainLogs(JSON.stringify(res, null, 2));
    } catch (e) {
      setTrainLogs("Training failed: " + e.message);
    } finally {
      setIsTraining(false);
    }
  };

  const isTrained = aiStatus?.is_trained ?? false;
  const lossHistory = aiStatus?.loss_history ?? [];

  return (
    <div>
      {/* AI Model Overview Banner */}
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <Cpu size={32} style={{ color: 'var(--accent-purple)' }} />
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Heterogeneous Graph Neural Network (HGNN)</h2>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWdith: '700px' }}>
            2-Layer GraphSAGE encoder capturing structural behavioral embeddings across <strong>User, Device, Location, and Resource</strong> nodes.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.75rem' }}>
          {isTrained ? (
            <span className="status-pill success" style={{ padding: '0.6rem 1.2rem', fontSize: '0.9rem' }}>
              <CheckCircle2 size={16} /> MODEL TRAINED & CHECKPOINTED
            </span>
          ) : (
            <span className="status-pill warning" style={{ padding: '0.6rem 1.2rem', fontSize: '0.9rem' }}>
              <AlertTriangle size={16} /> UNTRAINED (RANDOM INIT WEIGHTS)
            </span>
          )}

          <button 
            className="btn-primary" 
            onClick={handleTrainClick}
            disabled={isTraining}
            style={{ background: isTraining ? 'var(--text-muted)' : 'var(--gradient-cyber)' }}
          >
            {isTraining ? <RefreshCw className="animate-spin" size={16} /> : <Play size={16} />}
            {isTraining ? 'Training HGNN Model...' : 'Train / Pre-train HGNN Model Live'}
          </button>
        </div>
      </div>

      {/* Model Technical Metrics Grid */}
      <div className="kpi-grid" style={{ marginBottom: '2rem' }}>
        <div className="glass-card kpi-card">
          <div className="kpi-title">Network Architecture</div>
          <div className="kpi-value" style={{ fontSize: '1.2rem', color: 'var(--accent-cyan)' }}>
            HeteroConv + GraphSAGE
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Layer 1: 32 hidden | Layer 2: 16 out
          </div>
        </div>

        <div className="glass-card kpi-card">
          <div className="kpi-title">Total Trainable Parameters</div>
          <div className="kpi-value">{aiStatus?.total_parameters ?? 3488}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', marginTop: '0.5rem' }}>
            Embedding Dim: {aiStatus?.peer_embedding_dim ?? 16}
          </div>
        </div>

        <div className="glass-card kpi-card">
          <div className="kpi-title">Cached Role Baselines</div>
          <div className="kpi-value" style={{ fontSize: '1.2rem', color: 'var(--accent-purple)' }}>
            {aiStatus?.cached_roles?.length ? aiStatus.cached_roles.join(', ') : 'MARKETING, FINANCE, ENG, HR'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Federated Peer Mean & Std Vectors
          </div>
        </div>
      </div>

      {/* Training Output & Graph Topology Split */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Loss History & Output */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers style={{ color: 'var(--accent-cyan)' }} /> Training Loss History & Status
          </h3>

          {lossHistory.length > 0 ? (
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Loss trajectory across training epochs:
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--accent-emerald)', background: '#080b11', padding: '0.8rem', borderRadius: '6px' }}>
                {lossHistory.map((l, i) => `Epoch ${(i+1).toString().padStart(2, '0')}: Loss ${l}`).join('\n')}
              </div>
            </div>
          ) : (
            <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Click "Train HGNN Model Live" above to trigger self-supervised training!
            </div>
          )}

          {trainLogs && (
            <div style={{ marginTop: '1rem' }}>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>Training Response Log:</h4>
              <div className="json-box">{trainLogs}</div>
            </div>
          )}
        </div>

        {/* Heterogeneous Graph Node Types & Edge Schemas */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <GitBranch style={{ color: 'var(--accent-purple)' }} /> Heterogeneous Cyber Graph Schema
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
            <div style={{ background: 'rgba(18,24,36,0.8)', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <strong style={{ color: 'var(--accent-cyan)' }}>User Node (5 dim):</strong> One-hot Role (MARKETING, ENGINEERING, FINANCE, HR, UNKNOWN)
            </div>
            <div style={{ background: 'rgba(18,24,36,0.8)', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <strong style={{ color: 'var(--accent-purple)' }}>Device Node (11 dim):</strong> OS Family (6 dim) + Browser Family (5 dim)
            </div>
            <div style={{ background: 'rgba(18,24,36,0.8)', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <strong style={{ color: 'var(--accent-amber)' }}>Location Node (2 dim):</strong> Normalized Scaled Geo Lat & Lon
            </div>
            <div style={{ background: 'rgba(18,24,36,0.8)', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <strong style={{ color: 'var(--accent-pink)' }}>Resource Node (17 dim):</strong> Sensitivity score (1 dim) + SHA-256 URI hash (16 dim)
            </div>
            <div style={{ background: 'rgba(18,24,36,0.8)', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <strong style={{ color: 'var(--accent-emerald)' }}>Edge Types:</strong> <code>logged_in_from</code>, <code>accessed</code>, <code>located_in</code> (+ reverse edges)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
