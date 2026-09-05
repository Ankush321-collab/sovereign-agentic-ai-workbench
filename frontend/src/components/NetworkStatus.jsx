/**
 * components/NetworkStatus.jsx
 * Owner: Roshan
 * Sovereignty Dashboard - proves zero external calls during the SIH demo.
 */

import React, { useEffect, useState } from 'react';
import { getNetworkStatus, downloadAuditReport } from '../services/api';

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
  const [exporting, setExporting] = useState(false);

  function fetchStatus() {
    getNetworkStatus()
      .then(setStatus)
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30_000);
    return () => clearInterval(interval);
  }, []);

  const handleDownload = async () => {
    try {
      setExporting(true);
      await downloadAuditReport();
    } catch (err) {
      console.error(err);
    } finally {
      setExporting(false);
    }
  };

  const allGood = status &&
    status.external_connections === 0 &&
    status.internet_blocked;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <p className="section-label" style={{ margin: 0 }}>AIR-GAP SOVEREIGNTY</p>
        {status && (
          <button
            id="refresh-network-btn"
            className="btn btn-secondary btn-icon"
            onClick={fetchStatus}
            title="Refresh"
            style={{ fontSize: '0.7rem', padding: '2px 8px' }}
          >
            REFRESH
          </button>
        )}
      </div>

      {loading && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          <div className="spinner" /> Scanning process sockets...
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
              fontSize: '1rem',
              fontWeight: 800,
              letterSpacing: '0.05em',
              color: allGood ? 'var(--accent-green)' : 'var(--accent-red)',
              marginBottom: 4,
            }}>
              {allGood ? '[100% AIR-GAPPED]' : '[NETWORK ALERT]'}
            </div>
            <div style={{
              fontSize: '0.75rem', fontWeight: 700,
              color: allGood ? 'var(--accent-green)' : 'var(--accent-red)',
            }}>
              {allGood ? 'PROVEN ZERO EGRESS' : 'EXTERNAL SOCKET DETECTED'}
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 2 }}>
              {allGood ? 'No external sockets in process tree' : 'Review open connections'}
            </div>
          </div>

          {/* Stats */}
          <div>
            <StatRow
              label="External Sockets"
              value={status.external_connections}
              ok={status.external_connections === 0}
            />
            <StatRow
              label="Local Loopback Sockets"
              value={status.local_connections}
              ok={null}
            />
            <StatRow
              label="Internet Access"
              value={status.internet_blocked ? 'BLOCKED [SAFE]' : 'OPEN'}
              ok={status.internet_blocked}
            />
            <StatRow
              label="Firewall Mode"
              value={status.firewall_status || 'ZERO-EGRESS'}
              ok={true}
            />
          </div>

          {/* SHA-256 Audit Signature */}
          {status.audit_hash && (
            <div style={{
              marginTop: 8, padding: '0.45rem 0.6rem',
              background: 'rgba(59,130,246,0.06)',
              borderRadius: 6, fontSize: '0.68rem', color: 'var(--text-muted)',
              fontFamily: 'JetBrains Mono, monospace',
              wordBreak: 'break-all'
            }}>
              <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>SHA-256: </span>
              {status.audit_hash.substring(0, 16)}...
            </div>
          )}

          {/* Export Certificate Button */}
          <button
            onClick={handleDownload}
            disabled={exporting}
            style={{
              width: '100%',
              marginTop: 10,
              padding: '0.5rem',
              background: 'rgba(16,185,129,0.12)',
              border: '1px solid rgba(16,185,129,0.35)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--accent-green)',
              fontSize: '0.72rem',
              fontWeight: 700,
              cursor: 'pointer',
              letterSpacing: '0.03em'
            }}
          >
            {exporting ? 'Exporting...' : 'DOWNLOAD FORENSIC CERTIFICATE (JSON)'}
          </button>
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
