import React, { useState } from 'react';
import { getDownloadUrl } from '../services/api';

/**
 * Antigravity IDE / Claude Code Native UI Components
 * 1. Collapsible Thinking Block (`Thought for Xs`)
 * 2. Real Tool Action Widgets (Code Runner, Document Generator, Spreadsheet Builder)
 * 3. Instant Native Deliverable Download Cards
 */

export function ThinkingAccordion({ plan, router, ragSources, isStreaming }) {
  const [expanded, setExpanded] = useState(false);

  if (!plan && !router && (!ragSources || ragSources.length === 0)) return null;

  return (
    <div className="ag-thought-container">
      <div 
        className={`ag-thought-header ${expanded ? 'open' : ''}`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="ag-thought-left">
          <span className="ag-thought-icon">💭</span>
          <span className="ag-thought-title">
            {isStreaming ? 'Thinking...' : 'Thought process & grounding'}
          </span>
          {router?.model && (
            <span className="ag-thought-model">{router.model}</span>
          )}
        </div>
        <span className="ag-thought-chevron">{expanded ? '▲' : '▼'}</span>
      </div>

      {expanded && (
        <div className="ag-thought-body fade-in">
          {plan && (
            <div className="ag-thought-step">
              <span className="ag-thought-label">Execution Strategy</span>
              <p className="ag-thought-text">{plan.details || plan}</p>
            </div>
          )}

          {router && (
            <div className="ag-thought-step">
              <span className="ag-thought-label">Model Routing Rationale</span>
              <p className="ag-thought-text">
                Assigned to <strong>{router.model}</strong> ({router.task} specialist) — {router.reason}
              </p>
            </div>
          )}

          {ragSources && ragSources.length > 0 && (
            <div className="ag-thought-step">
              <span className="ag-thought-label">Local SOPs & Manuals Grounded</span>
              <div className="ag-thought-tags">
                {ragSources.map((src, i) => (
                  <span key={i} className="ag-thought-tag">
                    📖 {src.source || 'Knowledge Vault'} (P.{src.page || 1})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ToolActionPill({ toolName, args, result, stdout, code, isRunning }) {
  const [open, setOpen] = useState(false);

  const TOOL_INFO = {
    run_code: {
      name: 'run_python_sandbox',
      icon: '⚡',
      badge: 'Sandbox Execution',
      desc: 'Executed isolated Python script in sovereign sandbox'
    },
    generate_psu_note: {
      name: 'generate_psu_note',
      icon: '📄',
      badge: 'Word Document',
      desc: 'Compiled official PSU Secretariat Green-Sheet Note (.docx)'
    },
    edit_spreadsheet: {
      name: 'generate_spreadsheet',
      icon: '📊',
      badge: 'Excel Workbook',
      desc: 'Built styled engineering workbook with formulas (.xlsx)'
    },
    generate_pptx: {
      name: 'generate_presentation',
      icon: '📑',
      badge: 'PowerPoint Deck',
      desc: 'Compiled executive slide deck (.pptx)'
    },
    ocr_document: {
      name: 'ocr_and_vision_parser',
      icon: '🔍',
      badge: 'Multimodal OCR',
      desc: 'Extracted document text, tables, and P&ID tags'
    },
    search_knowledge_base: {
      name: 'search_sop_vault',
      icon: '📚',
      badge: 'Vector RAG',
      desc: 'Retrieved statutory engineering manuals'
    }
  };

  const meta = TOOL_INFO[toolName] || {
    name: toolName,
    icon: '🔧',
    badge: 'Tool Action',
    desc: 'Autonomous tool execution'
  };

  return (
    <div className={`ag-tool-card ${isRunning ? 'running' : 'done'}`}>
      <div className="ag-tool-header" onClick={() => setOpen(!open)}>
        <div className="ag-tool-meta">
          <span className="ag-tool-icon">{meta.icon}</span>
          <div className="ag-tool-titles">
            <div className="ag-tool-func">
              <code>{meta.name}</code>
              <span className="ag-tool-badge">{meta.badge}</span>
              {isRunning ? (
                <span className="ag-tool-status run">running...</span>
              ) : (
                <span className="ag-tool-status done">✓ completed</span>
              )}
            </div>
            <div className="ag-tool-desc">{meta.desc}</div>
          </div>
        </div>
        <button className="ag-tool-toggle">
          {open ? 'Collapse ▲' : 'Inspect ▼'}
        </button>
      </div>

      {open && (
        <div className="ag-tool-drawer fade-in">
          {code && (
            <div className="ag-drawer-block">
              <div className="ag-drawer-header">PYTHON CODE</div>
              <pre className="ag-drawer-pre python">
                <code>{code}</code>
              </pre>
            </div>
          )}

          {stdout && (
            <div className="ag-drawer-block">
              <div className="ag-drawer-header">SANDBOX TERMINAL OUTPUT (STDOUT)</div>
              <pre className="ag-drawer-pre stdout">
                <code>{stdout}</code>
              </pre>
            </div>
          )}

          {result && !stdout && (
            <div className="ag-drawer-block">
              <div className="ag-drawer-header">TOOL RESULT TELEMETRY</div>
              <pre className="ag-drawer-pre json">
                <code>{typeof result === 'object' ? JSON.stringify(result, null, 2) : String(result)}</code>
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function DeliverableCard({ file }) {
  const downloadUrl = getDownloadUrl(file.name);
  const ext = (file.type || file.name.split('.').pop() || '').toLowerCase();

  const EXT_ICONS = {
    docx: '📝',
    xlsx: '📊',
    pptx: '📑',
    pdf: '📄',
    py: '🐍',
    txt: '📃'
  };

  return (
    <div className="ag-deliverable-card fade-in">
      <div className="ag-deliv-icon">{EXT_ICONS[ext] || '📁'}</div>
      <div className="ag-deliv-info">
        <div className="ag-deliv-name">{file.name}</div>
        <div className="ag-deliv-meta">
          <span className="ag-deliv-type">{ext.toUpperCase()}</span>
          {file.size > 0 && <span>{(file.size / 1024).toFixed(1)} KB</span>}
          <span className="ag-deliv-ready">● Ready to Open</span>
        </div>
      </div>
      <a 
        href={downloadUrl}
        download={file.name}
        className="ag-deliv-btn"
      >
        ⤓ Download {file.name}
      </a>
    </div>
  );
}
