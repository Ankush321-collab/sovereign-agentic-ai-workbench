
import { useEffect, useState } from 'react';
import { getModels } from '../services/api';

const TASK_COLORS = {
  reasoning: 'var(--blue)',
  coding:    'var(--cyan)',
  vision:    'var(--purple)',
  document:  'var(--green)',
  general:   'var(--amber)',
};

function ScoreBar({ label, val, color }) {
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.67rem', color: 'var(--text-muted)', marginBottom: 3 }}>
        <span>{label}</span>
        <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{typeof val === 'number' ? val.toFixed(2) : val}</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${Math.min((val||0)*100, 100)}%`, background: color || 'var(--blue)' }} />
      </div>
    </div>
  );
}

export default function ModelRouting({ routingData }) {
  const [models,  setModels]  = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getModels()
      .then(d => setModels(Array.isArray(d?.models) ? d.models : Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const active = routingData;
  const accentColor = active ? (TASK_COLORS[active.task] || TASK_COLORS[active.task_type] || 'var(--blue)') : 'var(--blue)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {/* Active routing card */}
      {active ? (
        <div className="mcard fade-in" style={{ borderColor: `${accentColor}40` }}>
          <div style={{ fontSize: '.63rem', color: 'var(--text-muted)', marginBottom: 4 }}>SELECTED MODEL</div>
          <div className="mcard-name" style={{ color: accentColor }}>{active.model}</div>
          <div className="mcard-sub">{active.task || active.task_type || 'general'}</div>
          <div className="mcard-badges">
            <span className="badge b-green">LOCAL</span>
            {active.quantization && <span className="badge b-cyan">{active.quantization}</span>}
            {active.admitted_vram_gb && <span className="badge b-amber">{active.admitted_vram_gb} GB VRAM</span>}
          </div>
          {active.reason && (
            <div style={{
              marginTop: 10, padding: '8px 10px',
              background: 'var(--bg-base)', borderRadius: 'var(--r-md)',
              fontSize: '.72rem', color: 'var(--text-secondary)', lineHeight: 1.6,
              borderLeft: `2px solid ${accentColor}`,
            }}>
              {active.reason}
            </div>
          )}
          {active.score_breakdown && Object.keys(active.score_breakdown).length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: '.63rem', color: 'var(--text-muted)', marginBottom: 8, fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase' }}>Candidate Scores</div>
              {Object.entries(active.score_breakdown).map(([k, v]) => (
                <ScoreBar key={k} label={k} val={v} color={accentColor} />
              ))}
            </div>
          )}
        </div>
      ) : (
        <div style={{ fontSize: '.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
          Send a message to see routing decision
        </div>
      )}

      {/* Registered models list */}
      {loading ? (
        <div style={{ display: 'flex', gap: 7, alignItems: 'center', color: 'var(--text-muted)', fontSize: '.78rem' }}>
          <div className="spinner" /> Loading registry…
        </div>
      ) : models.length > 0 && (
        <div>
          <div className="card-head">Registry</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {models.map((m, i) => {
              const col = TASK_COLORS[m.task] || 'var(--blue)';
              return (
                <div key={i} className="mcard" style={{ padding: '8px 10px', borderColor: `${col}28` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div className="mcard-name" style={{ fontSize: '.78rem', color: col }}>{m.name || m.id}</div>
                    <span className={`badge ${m.healthy || m.enabled ? 'b-green' : 'b-red'}`}>
                      {m.healthy || m.enabled ? 'ON' : 'OFF'}
                    </span>
                  </div>
                  <div className="mcard-sub">{m.task} · {m.quant || 'q4_k_m'}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
