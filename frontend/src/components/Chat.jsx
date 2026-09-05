
/**
 * Chat.jsx  —  Main conversational interface
 * Sends messages, shows typing indicator, lifts state to Dashboard
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { runAgent, routeQuery } from '../services/api';

const SUGGESTIONS = [
  'Calculate pipe wall thickness per ASME B31.3',
  'Draft a PSU approval note for valve replacement',
  'Analyse the uploaded P&ID drawing',
  'Compare SOP compliance for HPCL shutdown procedure',
];

function fmtTime(d) {
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

export default function Chat({ onResponse, uploadedFile, onClearFile }) {
  const [messages, setMessages] = useState([]);
  const [input,    setInput]    = useState('');
  const [loading,  setLoading]  = useState(false);
  const bottomRef  = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 180) + 'px';
  }, [input]);

  const send = useCallback(async (text) => {
    const query = (text || input).trim();
    if (!query || loading) return;
    setInput('');

    const userMsg = { role: 'user', text: query, ts: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await runAgent(query, uploadedFile?.file_id ?? null);

      // Derive display text from response
      const answer = data.answer
        ?? data.response
        ?? data.final_response
        ?? data.output
        ?? 'Task completed. Check the Pipeline tab for execution trace.';

      // Extract routing from response if available
      const routingRes = data.routing ?? data.route ?? null;
      const modelName  = data.selected_model ?? routingRes?.model ?? 'Qwen2.5-7B';

      const aiMsg = {
        role:  'ai',
        text:  answer,
        ts:    new Date(),
        model: modelName,
      };
      setMessages(prev => [...prev, aiMsg]);

      // Lift data to Dashboard
      if (onResponse) onResponse({
        routing: routingRes ?? { model: modelName, task: data.task_class ?? 'general', reason: data.routing_reason ?? '' },
        trace:   data.audit_log ?? data.trace ?? [],
        sources: data.sources   ?? [],
        files:   data.generated_files ?? data.files ?? [],
      });
    } catch (err) {
      const errMsg = { role: 'ai', text: `⚠️ ${err.message}`, ts: new Date(), isError: true };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, uploadedFile, onResponse]);

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <>
      <div className="chat-msgs" id="chat-messages">
        <div className="chat-msgs-inner">
          {messages.length === 0 && !loading && (
            <div className="chat-welcome">
              <div className="welcome-icon">🛡</div>
              <div className="welcome-title">VAJRA Sovereign AI Workbench</div>
              <div className="welcome-sub">
                100% air-gapped · All computation on-premises · No external egress
              </div>
              <div className="chips">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} className="chip" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`msg-row ${m.role}`}>
              <div className={`msg-avatar ${m.role === 'user' ? 'av-user' : 'av-ai'}`}>
                {m.role === 'user' ? 'U' : 'VJ'}
              </div>
              <div className="msg-body">
                <div className={`msg-text${m.isError ? ' error' : ''}`}
                  style={m.isError ? { borderColor: 'rgba(239,68,68,.3)', color: 'var(--red)' } : {}}
                >
                  {m.text}
                </div>
                <div className="msg-meta">
                  <span>{fmtTime(m.ts)}</span>
                  {m.model && <span className="model-pill">{m.model}</span>}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="msg-row ai">
              <div className="msg-avatar av-ai">VJ</div>
              <div className="msg-body">
                <div className="typing">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="input-wrap">
        <div className="input-inner">
          <div className="input-box">
            <textarea
              ref={textareaRef}
              id="chat-input"
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKey}
              placeholder="Ask anything… (Shift+Enter for newline)"
              disabled={loading}
            />
            <div className="input-toolbar">
              <button className={`icon-btn send-btn`} onClick={() => send()} disabled={!input.trim() || loading} title="Send">
                {loading ? <div className="spinner" /> : '↑'}
              </button>
            </div>
          </div>
          <div className="input-foot">
            <span className="input-hint">
              Powered by local Ollama models · Zero external egress guaranteed
            </span>
            {uploadedFile && (
              <div className="file-pill">
                📎 {uploadedFile.name || uploadedFile.file_id}
                <span className="file-pill-x" onClick={onClearFile}>✕</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
