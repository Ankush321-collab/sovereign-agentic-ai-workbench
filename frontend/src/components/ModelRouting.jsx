/**
 * components/ModelRouting.jsx
 * Owner: Roshan
 * Displays which model was selected and why (from Aarav's router).
 */

import { useEffect, useState } from 'react';
import { getRouting } from '../services/api';

const MODEL_META = {
  'qwen2.5:7b-instruct':  { label: 'Qwen Text',   type: 'Reasoning / Document', color: 'var(--accent-blue)',   badge: 'badge-blue' },
  'qwen2.5vl:7b':         { label: 'Qwen Vision', type: 'Vision / Image / OCR', color: 'var(--accent-purple)', badge: 'badge-purple' },
  'qwen2.5-coder:latest': { label: 'Qwen Coder',  type: 'Coding / Debugging',   color: 'var(--accent-amber)',  badge: 'badge-amber' },
};

const TASK_ICONS = {
  document:  '📄',
  coding:    '💻',
  vision:    '🖼️',
  reasoning: '🧠',
  general:   '💬',
};

export default function ModelRouting({ routingData }) {
  const [routing, setRouting] = useState(null);
  const [loading, setLoading] = useState(true);

  // On mount: fetch current routing
  useEffect(() => {
    getRouting()
      .then(setRouting)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // When chat response comes in with updated routing
  useEffect(() => {
    if (routingData) setRouting(routingData);
  }, [routingData]);

  const meta = routing ? (MODEL_META[routing.model] || {
    label: routing.model,
    type: routing.task_type,
    color: 'var(--accent-cyan)',
    badge: 'badge-cyan',
  }) : null;

  return (
    <div>
      <p className="section-label">Model Routing</p>

      {loading && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          <div className="spinner" /> Loading…
        </div>
      )}

      {!loading && routing && (
        <div className="fade-in">
          {/* Model name */}
          <div style={{
            padding: '0.65rem 0.85rem',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: `1px solid ${meta.color}30`,
            marginBottom: 10,
          }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 3 }}>Selected Model</div>
            <div style={{
              fontSize: '1rem', fontWeight: 700,
              color: meta.color, fontFamily: 'JetBrains Mono, monospace',
            }}>
              {meta.label}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
              {meta.type}
            </div>
          </div>

          {/* Task type */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'center' }}>
            <span style={{ fontSize: '1rem' }}>{TASK_ICONS[routing.task_type] || '▸'}</span>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Task Type</div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'capitalize' }}>
                {routing.task_type}
              </div>
            </div>
          </div>

          {/* Reason */}
          <div style={{
            padding: '0.5rem 0.75rem',
            background: 'rgba(6,182,212,0.05)',
            borderRadius: 6,
            borderLeft: '2px solid var(--accent-cyan)',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
            marginBottom: 10,
          }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>Reason: </span>
            {routing.reason || routing.routing_reason}
          </div>

          {/* Execution badge */}
          <div style={{ display: 'flex', gap: 6 }}>
            <span className="badge badge-green">⚡ LOCAL</span>
            <span className={`badge ${meta.badge}`}>{meta.label}</span>
          </div>
        </div>
      )}

      {!loading && !routing && (
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          No routing data yet. Send a message to see the routing decision.
        </div>
      )}
    </div>
  );
}
