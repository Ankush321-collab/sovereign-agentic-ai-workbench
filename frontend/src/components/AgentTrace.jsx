/**
 * components/AgentTrace.jsx
 * Owner: Roshan
 * Displays the step-by-step agent execution trace from LangGraph.
 */

import { useEffect, useState } from 'react';

const STATUS_COLORS = {
  success: 'var(--accent-green)',
  running: 'var(--accent-cyan)',
  pending: 'var(--text-muted)',
  error:   'var(--accent-red)',
};

const STEP_ICONS = {
  Planner:    '🧠',
  Router:     '🔀',
  RAG:        '📚',
  Tool:       '🔧',
  Reflection: '🔍',
  Finalizer:  '✅',
};

const DEFAULT_TRACE = [
  { step: 'Planner',    action: 'Waiting for user query…', status: 'pending' },
  { step: 'Router',     action: 'Waiting…',                status: 'pending' },
  { step: 'RAG',        action: 'Waiting…',                status: 'pending' },
  { step: 'Tool',       action: 'Waiting…',                status: 'pending' },
  { step: 'Reflection', action: 'Waiting…',                status: 'pending' },
  { step: 'Finalizer',  action: 'Waiting…',                status: 'pending' },
];

function TraceStep({ step, action, status, index, visible }) {
  return (
    <div
      className={visible ? 'fade-in' : ''}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 10,
        padding: '0.5rem 0',
        opacity: status === 'pending' ? 0.45 : 1,
        transition: 'opacity 0.3s',
        animationDelay: `${index * 0.07}s`,
        animationFillMode: 'both',
      }}
    >
      {/* Timeline dot */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 2 }}>
        <div style={{
          width: 10, height: 10, borderRadius: '50%',
          background: STATUS_COLORS[status] || 'var(--text-muted)',
          flexShrink: 0,
          boxShadow: status === 'success'
            ? `0 0 6px ${STATUS_COLORS.success}`
            : status === 'running'
            ? `0 0 6px ${STATUS_COLORS.running}`
            : 'none',
        }} className={status === 'running' ? 'pulse' : ''} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: '0.75rem' }}>{STEP_ICONS[step] || '▸'}</span>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>{step}</span>
          {status === 'success' && (
            <span style={{ fontSize: '0.65rem', color: 'var(--accent-green)' }}>✓</span>
          )}
          {status === 'error' && (
            <span style={{ fontSize: '0.65rem', color: 'var(--accent-red)' }}>✗</span>
          )}
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 1 }}>
          {action}
        </div>
      </div>
    </div>
  );
}

export default function AgentTrace({ trace }) {
  const [displayTrace, setDisplayTrace] = useState(DEFAULT_TRACE);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (trace && trace.length > 0) {
      setVisible(true);
      setDisplayTrace(trace);
    } else {
      setDisplayTrace(DEFAULT_TRACE);
      setVisible(false);
    }
  }, [trace]);

  const doneCount  = displayTrace.filter((s) => s.status === 'success').length;
  const totalCount = displayTrace.length;
  const progress   = totalCount > 0 ? (doneCount / totalCount) * 100 : 0;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <p className="section-label" style={{ margin: 0 }}>Agent Trace</p>
        {visible && (
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            {doneCount}/{totalCount}
          </span>
        )}
      </div>

      {/* Progress bar */}
      {visible && (
        <div style={{
          height: 3, background: 'var(--border)',
          borderRadius: 2, marginBottom: 10, overflow: 'hidden',
        }}>
          <div style={{
            height: '100%', width: `${progress}%`,
            background: 'linear-gradient(90deg,var(--accent-blue),var(--accent-cyan))',
            borderRadius: 2, transition: 'width 0.5s ease',
          }} />
        </div>
      )}

      {/* Steps */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {displayTrace.map((step, i) => (
          <TraceStep key={i} {...step} index={i} visible={visible} />
        ))}
      </div>
    </div>
  );
}
