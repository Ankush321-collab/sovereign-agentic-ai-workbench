/**
 * pages/Dashboard.jsx
 * Owner: Roshan
 * Main layout: 3-column grid with Chat (left), sidebar panels (right).
 */

import { useState } from 'react';
import Chat           from '../components/Chat';
import FileUpload     from '../components/FileUpload';
import AgentTrace     from '../components/AgentTrace';
import ModelRouting   from '../components/ModelRouting';
import Sources        from '../components/Sources';
import GeneratedFiles from '../components/GeneratedFiles';
import NetworkStatus  from '../components/NetworkStatus';

// ── Header ───────────────────────────────────────────────────────────────────
function Header() {
  return (
    <header style={{
      height: 56,
      background: 'rgba(15,22,41,0.95)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 1.5rem',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      {/* Logo / title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: 'linear-gradient(135deg,#3b82f6,#06b6d4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '1rem',
        }}>
          🛡️
        </div>
        <div>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
            <span className="glow-text">Sovereign AI</span>{' '}
            <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>Workbench</span>
          </div>
          <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', letterSpacing: '0.06em' }}>
            SIH 2026 · TEAM QUANTA CODES
          </div>
        </div>
      </div>

      {/* Status pills */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <span className="badge badge-green">
          <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor' }} className="pulse" />
          LOCAL AI
        </span>
        <span className="badge badge-cyan">OFFLINE SAFE</span>
      </div>
    </header>
  );
}

// ── Panel wrapper ─────────────────────────────────────────────────────────────
function Panel({ children, style = {} }) {
  return (
    <div className="card" style={{ ...style }}>
      {children}
    </div>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [uploadedFile,  setUploadedFile]  = useState(null);
  const [agentTrace,    setAgentTrace]    = useState(null);
  const [routingData,   setRoutingData]   = useState(null);
  const [ragSources,    setRagSources]    = useState([]);
  const [generatedFiles, setGeneratedFiles] = useState([]);

  function handleChatResponse(data) {
    if (data.trace)   setAgentTrace(data.trace);
    if (data.sources) setRagSources(data.sources);
    if (data.files)   setGeneratedFiles(data.files);
    if (data.model || data.task_type) {
      setRoutingData({
        model:        data.model,
        task_type:    data.task_type,
        reason:       data.routing_reason,
        execution:    'LOCAL',
      });
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      <Header />

      <main style={{
        display: 'grid',
        gridTemplateColumns: '1fr 300px',
        gridTemplateRows: 'auto',
        gap: '1rem',
        padding: '1rem 1.25rem',
        maxWidth: 1400,
        margin: '0 auto',
        height: 'calc(100vh - 56px)',
        boxSizing: 'border-box',
      }}>

        {/* ── Left column: Chat ─────────────────────────── */}
        <Panel style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0 }}>
          <Chat onResponse={handleChatResponse} uploadedFile={uploadedFile} />
        </Panel>

        {/* ── Right column: Sidebar panels ──────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', overflowY: 'auto' }}>

          {/* File Upload */}
          <Panel>
            <FileUpload onUpload={setUploadedFile} />
          </Panel>

          {/* Model Routing */}
          <Panel>
            <ModelRouting routingData={routingData} />
          </Panel>

          {/* Agent Trace */}
          <Panel>
            <AgentTrace trace={agentTrace} />
          </Panel>

          {/* RAG Sources */}
          <Panel>
            <Sources sources={ragSources} />
          </Panel>

          {/* Generated Files */}
          <Panel>
            <GeneratedFiles newFiles={generatedFiles} />
          </Panel>

          {/* Network Status */}
          <Panel>
            <NetworkStatus />
          </Panel>

        </div>
      </main>
    </div>
  );
}
