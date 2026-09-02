/**
 * components/NetworkStatus.jsx
 * Owner: Roshan
 * Sovereignty Dashboard — proves zero external calls during the SIH demo.
 */

import { useEffect, useState } from 'react';
import { getNetworkStatus } from '../services/api';

function StatRow({ label, value, ok }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '0.45rem 0', borderBottom: '1px solid var(--border)',
    }}>
      <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{label}</span>
      <span style={{
        fontSize: '0.78rem', fontWeight: 700,
        color: ok === true
          ? 'var(--accent-green)'
          : ok === false
          ? 'var(--accent-red)'
          : 'var(--text-primary)',
      }}>
        {value}
      </span>
    </div>
  );
}

export default function NetworkStatus() {
  const [status, setStatus]   = useState(null);
  const [loading, setLoading] = useState(true);

  function fetchStatus() {
    getNetworkStatus()
      .then(setStatus)
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchStatus();
    // Poll every 30 seconds
    const interval = setInterval(fetchStatus, 30_000);
    return () => clearInterval(interval);
  }, []);

  const allGood = status &&
    status.external_connections === 0 &&
    status.internet_blocked &&
    status.models_local &&
    status.processing_local;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <p className="section-label" style={{ margin: 0 }}>🔒 Sovereignty</p>
        {status && (
          <button
            id="refresh-network-btn"
            className="btn btn-secondary btn-icon"
            onClick={fetchStatus}
            title="Refresh"
            style={{ fontSize: '0.7rem', padding: '2px 8px' }}
          >
            ↺
          </button>
        )}
      </div>

      {loading && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          <div className="spinner" /> Checking…
        </div>
      )}

      {!loading && status && (
        <div className="fade-in">
          {/* Big status indicator */}
          <div style={{
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            background: allGood
              ? 'rgba(16,185,129,0.08)'
              : 'rgba(239,68,68,0.08)',
            border: `1px solid ${allGood ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.25)'}`,
            textAlign: 'center',
            marginBottom: 10,
          }}>
            <div style={{
              fontSize: '1.5rem',
              marginBottom: 4,
            }}>
              {allGood ? '🛡️' : '⚠️'}
            </div>
            <div style={{
              fontSize: '0.8rem', fontWeight: 700,
              color: allGood ? 'var(--accent-green)' : 'var(--accent-red)',
            }}>
              {allGood ? 'FULLY SOVEREIGN' : 'CHECK REQUIRED'}
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 2 }}>
              {allGood ? 'Zero external calls detected' : 'Review network connections'}
            </div>
          </div>

          {/* Stats */}
          <div>
            <StatRow
              label="External Connections"
              value={status.external_connections}
              ok={status.external_connections === 0}
            />
            <StatRow
              label="Local Connections"
              value={status.local_connections}
              ok={null}
            />
            <StatRow
              label="Internet Access"
              value={status.internet_blocked ? 'BLOCKED ✓' : 'OPEN ✗'}
              ok={status.internet_blocked}
            />
            <StatRow
              label="AI Models"
              value={status.models_local ? 'LOCAL ✓' : 'CLOUD ✗'}
              ok={status.models_local}
            />
            <StatRow
              label="Data Processing"
              value={status.processing_local ? 'LOCAL ONLY ✓' : 'EXTERNAL ✗'}
              ok={status.processing_local}
            />
          </div>

          {/* Ollama info */}
          <div style={{
            marginTop: 8, padding: '0.4rem 0.6rem',
            background: 'rgba(59,130,246,0.06)',
            borderRadius: 6, fontSize: '0.7rem', color: 'var(--text-muted)',
            fontFamily: 'JetBrains Mono, monospace',
          }}>
            Ollama · localhost:11434
          </div>
        </div>
      )}

      {!loading && !status && (
        <div style={{ fontSize: '0.8rem', color: 'var(--accent-red)' }}>
          Could not fetch network status.
        </div>
      )}
    </div>
  );
}
