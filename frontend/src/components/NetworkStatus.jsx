
import { useEffect, useState } from 'react';
import { getNetworkStatus, downloadAuditReport } from '../services/api';

export default function NetworkStatus({ onStatusChange }) {
  const [status,    setStatus]    = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [exporting, setExporting] = useState(false);

  function fetch_() {
    setLoading(true);
    getNetworkStatus()
      .then(d => { setStatus(d); onStatusChange?.(d.internet_blocked && d.external_connections === 0); })
      .catch(() => { setStatus(null); onStatusChange?.(false); })
      .finally(() => setLoading(false));
  }

  useEffect(() => { fetch_(); const t = setInterval(fetch_, 30000); return () => clearInterval(t); }, []);

  const ok = status && status.external_connections === 0 && status.internet_blocked;

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
      {loading && (
        <div style={{ display:'flex', gap:7, alignItems:'center', color:'var(--text-muted)', fontSize:'.78rem' }}>
          <div className="spinner" /> Scanning sockets…
        </div>
      )}

      {!loading && status && (
        <>
          <div className={`sov-banner ${ok ? 'sov-ok' : 'sov-alert'}`}>
            <span style={{ fontSize:18 }}>{ok ? '🛡' : '⚠'}</span>
            <div>
              <div>{ok ? '100% AIR-GAPPED' : 'NETWORK ALERT'}</div>
              <div style={{ fontSize:'.7rem', fontWeight:400, marginTop:1, opacity:.85 }}>
                {ok ? 'Zero external egress verified' : 'External socket detected'}
              </div>
            </div>
          </div>

          <div className="card" style={{ padding:'10px 13px' }}>
            <div className="stat-row">
              <span className="stat-label">External Sockets</span>
              <span className={`stat-val ${status.external_connections === 0 ? 'ok' : 'err'}`}>
                {status.external_connections}
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Loopback Sockets</span>
              <span className="stat-val">{status.local_connections}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Internet</span>
              <span className={`stat-val ${status.internet_blocked ? 'ok' : 'err'}`}>
                {status.internet_blocked ? 'BLOCKED' : 'OPEN'}
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Firewall</span>
              <span className="stat-val ok">{status.firewall_status || 'ZERO-EGRESS'}</span>
            </div>
          </div>

          {status.audit_hash && (
            <div style={{
              padding:'8px 10px', background:'var(--bg-base)', borderRadius:'var(--r-md)',
              fontFamily:'var(--font-mono)', fontSize:'.67rem', color:'var(--text-muted)',
              wordBreak:'break-all', border:'1px solid var(--border)',
            }}>
              <span style={{ color:'var(--cyan)', fontWeight:600 }}>SHA-256 </span>
              {status.audit_hash}
            </div>
          )}

          <div style={{ display:'flex', gap:8 }}>
            <button className="btn btn-ghost btn-sm" onClick={fetch_} style={{ flex:1, justifyContent:'center' }}>
              ↻ Refresh
            </button>
            <button
              className="btn btn-ghost btn-sm"
              style={{ flex:1, justifyContent:'center', color:'var(--green)', borderColor:'rgba(16,185,129,.3)' }}
              disabled={exporting}
              onClick={async () => { setExporting(true); await downloadAuditReport().catch(console.error); setExporting(false); }}
            >
              {exporting ? 'Exporting…' : '⬇ Certificate'}
            </button>
          </div>
        </>
      )}

      {!loading && !status && (
        <div style={{ fontSize:'.8rem', color:'var(--red)' }}>
          ⚠ Could not reach backend at localhost:8000
        </div>
      )}
    </div>
  );
}
