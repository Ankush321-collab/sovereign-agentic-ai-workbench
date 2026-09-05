
import { useEffect, useState } from 'react';

const ICONS = { Planner:'🧠', Router:'🔀', RAG:'📚', Tool:'🔧', PolicyGate:'🛡', Reflection:'🔍', Finalizer:'✅' };
const DEFAULT = [
  { step: 'Planner',    action: 'Awaiting query…', status: 'off' },
  { step: 'Router',     action: 'Awaiting…',       status: 'off' },
  { step: 'RAG',        action: 'Awaiting…',       status: 'off' },
  { step: 'PolicyGate', action: 'Awaiting…',       status: 'off' },
  { step: 'Tool',       action: 'Awaiting…',       status: 'off' },
  { step: 'Reflection', action: 'Awaiting…',       status: 'off' },
  { step: 'Finalizer',  action: 'Awaiting…',       status: 'off' },
];

function dotClass(s) {
  if (s === 'success' || s === 'ok') return 'ok';
  if (s === 'running')               return 'run';
  if (s === 'error')                 return 'err';
  return 'off';
}

export default function AgentTrace({ trace }) {
  const [items, setItems] = useState(DEFAULT);

  useEffect(() => {
    setItems(trace && trace.length > 0 ? trace : DEFAULT);
  }, [trace]);

  const done     = items.filter(i => i.status === 'success' || i.status === 'ok').length;
  const progress = items.length > 0 ? (done / items.length) * 100 : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Progress */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.68rem', color: 'var(--text-muted)', marginBottom: 5 }}>
          <span style={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.07em' }}>Pipeline</span>
          <span>{done}/{items.length} steps</span>
        </div>
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Timeline */}
      <div className="tl">
        {items.map((item, i) => (
          <div key={i} className="tl-item">
            <div className="tl-left">
              <div className={`tl-dot ${dotClass(item.status)}`} />
              {i < items.length - 1 && <div className="tl-line" />}
            </div>
            <div className="tl-body fade-in" style={{ animationDelay: `${i * 0.05}s` }}>
              <div className="tl-name" style={{ opacity: item.status === 'off' ? 0.4 : 1 }}>
                <span>{ICONS[item.step] || '▸'}</span>
                {item.step}
                {(item.status === 'success' || item.status === 'ok') && (
                  <span style={{ fontSize: '.65rem', color: 'var(--green)' }}>✓</span>
                )}
                {item.status === 'error' && (
                  <span style={{ fontSize: '.65rem', color: 'var(--red)' }}>✗</span>
                )}
              </div>
              <div className="tl-desc" style={{ opacity: item.status === 'off' ? 0.35 : 0.85 }}>
                {item.action || item.details || '—'}
              </div>
              {item.status !== 'off' && item.timestamp && (
                <div style={{ fontSize: '.63rem', color: 'var(--text-disabled)', marginTop: 2 }}>
                  {new Date(item.timestamp).toLocaleTimeString('en-IN')}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
