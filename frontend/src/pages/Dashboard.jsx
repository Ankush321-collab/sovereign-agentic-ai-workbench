
/**
 * Dashboard.jsx  —  VAJRA Sovereign AI Workbench
 * Layout: Left Sidebar | Chat Column | Right Panel
 */
import { useState, useCallback } from 'react';
import Chat from '../components/Chat';
import FileUpload from '../components/FileUpload';
import ModelRouting from '../components/ModelRouting';
import AgentTrace from '../components/AgentTrace';
import Sources from '../components/Sources';
import GeneratedFiles from '../components/GeneratedFiles';
import NetworkStatus from '../components/NetworkStatus';

const NAV = [
  { id: 'chat',    label: 'Chat',         icon: '💬' },
  { id: 'rag',     label: 'RAG Ingest',   icon: '📚' },
  { id: 'audit',   label: 'Audit Logs',   icon: '🛡' },
];

const TABS = ['Model', 'Pipeline', 'Sources', 'Files', 'Network'];

export default function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [panelOpen,   setPanelOpen]   = useState(true);
  const [activeNav,   setActiveNav]   = useState('chat');
  const [activeTab,   setActiveTab]   = useState('Model');

  // Lifted state from Chat responses
  const [routingData,    setRoutingData]    = useState(null);
  const [agentTrace,     setAgentTrace]     = useState([]);
  const [ragSources,     setRagSources]     = useState([]);
  const [generatedFiles, setGeneratedFiles] = useState([]);
  const [uploadedFile,   setUploadedFile]   = useState(null);
  const [networkOk,      setNetworkOk]      = useState(true);

  const onChatResponse = useCallback((data) => {
    if (data.routing)       setRoutingData(data.routing);
    if (data.trace)         setAgentTrace(data.trace);
    if (data.sources)       setRagSources(data.sources);
    if (data.files)         setGeneratedFiles(data.files);
    // Auto-switch panel tab to Pipeline after response
    setActiveTab('Pipeline');
  }, []);

  return (
    <div className="app-shell">
      {/* ── Sidebar ──────────────────────────────────────────── */}
      <aside className={`sidebar${sidebarOpen ? '' : ' hidden'}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">VJ</div>
          <div className="sidebar-brand">
            VAJRA<small>Sovereign AI · SIH 2026</small>
          </div>
        </div>
        <div className="sidebar-body">
          <div className="sidebar-sep">Workspace</div>
          {NAV.map(n => (
            <button
              key={n.id}
              className={`nav-btn${activeNav === n.id ? ' active' : ''}`}
              onClick={() => setActiveNav(n.id)}
            >
              <span className="nav-icon">{n.icon}</span>
              {n.label}
            </button>
          ))}

          <div className="sidebar-sep" style={{ marginTop: 8 }}>Upload</div>
          <FileUpload onUpload={setUploadedFile} compact />
        </div>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 2px' }}>
            <div className={`dot dot-${networkOk ? 'green' : 'red'}`} />
            <span style={{ fontSize: '.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              {networkOk ? '100% Air-Gapped' : 'Network Alert'}
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main area ────────────────────────────────────────── */}
      <div className="main-col">
        {/* Topbar */}
        <header className="topbar">
          <button className="topbar-btn" onClick={() => setSidebarOpen(v => !v)} title="Toggle sidebar">
            ☰
          </button>
          <span className="topbar-title">
            {activeNav === 'chat'  && 'Agentic Chat'}
            {activeNav === 'rag'   && 'RAG Knowledge Base'}
            {activeNav === 'audit' && 'Audit Logs'}
          </span>
          <div className="topbar-right">
            <div className={`dot dot-${networkOk ? 'green' : 'red'}`} />
            <span className="topbar-label">AIR-GAPPED</span>
            <div style={{ width: 1, height: 16, background: 'var(--border)', margin: '0 4px' }} />
            <button className="topbar-btn" onClick={() => setPanelOpen(v => !v)} title="Toggle panel" style={{ fontSize: '14px' }}>
              ⊞
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="content-row">
          <div className="chat-col">
            <Chat
              onResponse={onChatResponse}
              uploadedFile={uploadedFile}
              onClearFile={() => setUploadedFile(null)}
            />
          </div>

          {/* ── Right Panel ───────────────────────────────────── */}
          <aside className={`right-col${panelOpen ? '' : ' hidden'}`}>
            <div className="ptabs">
              {TABS.map(t => (
                <button
                  key={t}
                  className={`ptab${activeTab === t ? ' on' : ''}`}
                  onClick={() => setActiveTab(t)}
                >
                  {t}
                </button>
              ))}
            </div>
            <div className="pbody">
              {activeTab === 'Model'    && <ModelRouting routingData={routingData} />}
              {activeTab === 'Pipeline' && <AgentTrace   trace={agentTrace} />}
              {activeTab === 'Sources'  && <Sources      sources={ragSources} />}
              {activeTab === 'Files'    && <GeneratedFiles newFiles={generatedFiles} />}
              {activeTab === 'Network'  && <NetworkStatus onStatusChange={setNetworkOk} />}
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
