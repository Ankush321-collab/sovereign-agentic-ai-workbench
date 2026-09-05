/**
 * components/ModelRouting.jsx
 * Owner: Roshan
 * Displays multi-stage explainable model routing decision (from Aarav's router).
 */

import React, { useEffect, useState } from 'react';
import { getRouting } from '../services/api';

const MODEL_META = {
  'qwen-reasoning': { label: 'Qwen Reasoning', type: 'Reasoning / Document', color: 'var(--accent-blue)', badge: 'badge-blue' },
  'qwen-coder':     { label: 'Qwen Coder',     type: 'Coding / ASME Calc',    color: 'var(--accent-amber)', badge: 'badge-amber' },
  'qwen-vl':        { label: 'Qwen Vision',    type: 'Vision / P&ID / NDT',   color: 'var(--accent-purple)', badge: 'badge-purple' },
};

export default function ModelRouting({ routingData }) {
  const [routing, setRouting] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRouting()
      .then((data) => {
        if (data && data.models && data.models.length > 0) {
          setRouting({
            model: data.models[0].name,
            task_type: data.models[0].task,
            task_class: 'engineering_calc',
            reason: 'Primary configured model for on-premises engineering pipeline'
          });
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

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
      <p className="section-label">EXPLAINABLE ROUTING</p>

      {loading && (
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          <div className="spinner" /> Loading routing priors...
        </div>
      )}

      {!loading && routing && (
        <div className="fade-in">
          {/* Model Card */}
          <div style={{
            padding: '0.65rem 0.85rem',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: `1px solid ${meta ? meta.color : 'var(--accent-cyan)'}40`,
            marginBottom: 10,
          }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 3 }}>Selected Model</div>
            <div style={{
              fontSize: '1rem', fontWeight: 700,
              color: meta ? meta.color : 'var(--accent-cyan)', fontFamily: 'JetBrains Mono, monospace',
            }}>
              {meta ? meta.label : routing.model}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
              {meta ? meta.type : routing.task_type}
            </div>
          </div>

          {/* Fine-grained Task Class */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Classified Task:</span>
            <span className="badge badge-blue" style={{ textTransform: 'uppercase', fontSize: '0.68rem' }}>
              {routing.task_class || routing.task_type}
            </span>
          </div>

          {/* Explainability / Reason */}
          <div style={{
            padding: '0.5rem 0.75rem',
            background: 'rgba(6,182,212,0.05)',
            borderRadius: 6,
            borderLeft: '2px solid var(--accent-cyan)',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.4,
            marginBottom: 10,
          }}>
            <div style={{ color: 'var(--accent-cyan)', fontWeight: 600, fontSize: '0.68rem', marginBottom: 2 }}>
              Stage 1 Explainability:
            </div>
            {routing.reason || 'Optimal capability match based on task featurization'}
          </div>

          {/* Scores Breakdown if available */}
          {routing.score_breakdown && Object.keys(routing.score_breakdown).length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: 4 }}>Candidate Scores:</div>
              {Object.entries(routing.score_breakdown).map(([mName, score]) => (
                <div key={mName} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', padding: '1px 0' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{mName}</span>
                  <span style={{ fontWeight: 600, color: 'var(--accent-green)' }}>{score}</span>
                </div>
              ))}
            </div>
          )}

          {/* Badges */}
          <div style={{ display: 'flex', gap: 6 }}>
            <span className="badge badge-green">LOCAL WEIGHTS</span>
            <span className="badge badge-cyan">{routing.quantization || 'Q4_K_M'}</span>
            {routing.admitted_vram_gb && (
              <span className="badge badge-amber">{routing.admitted_vram_gb} GB VRAM</span>
            )}
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
