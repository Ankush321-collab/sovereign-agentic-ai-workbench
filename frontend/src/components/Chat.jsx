import React, { useState, useRef, useEffect, useCallback } from 'react';
import { streamAgent, runAgent } from '../services/api';
import MarkdownRenderer from './MarkdownRenderer';
import { ThinkingAccordion, ToolActionPill, DeliverableCard } from './AgentActionPill';

const SUGGESTIONS = [
  'Calculate pipe wall thickness per ASME B31.3 for flange FL-402 and generate approval note',
  'Draft an official PSU Secretariat Green-Sheet approval note for valve replacement',
  'Analyse P&ID diagram and export equipment schedule to Excel spreadsheet',
  'Perform remaining life calculation and generate executive briefing slides (.pptx)',
];

function fmtTime(d) {
  return d ? new Date(d).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '';
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

    const userMsg = {
      role: 'user',
      text: query,
      ts: new Date(),
      file: uploadedFile ? { name: uploadedFile.name, size: uploadedFile.size } : null
    };

    const aiMsgId = Date.now();
    const initialAiMsg = {
      id: aiMsgId,
      role: 'ai',
      text: '',
      ts: new Date(),
      model: 'qwen2.5:7b-instruct',
      plan: null,
      router: null,
      ragSources: [],
      toolCalls: [],
      deliverables: [],
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMsg, initialAiMsg]);
    setLoading(true);

    const updateCurrentAiMsg = (updater) => {
      setMessages(prev => prev.map(msg => msg.id === aiMsgId ? updater(msg) : msg));
    };

    try {
      await streamAgent(
        query,
        uploadedFile?.file_id ?? null,
        // onEvent
        ({ event, data }) => {
          if (event === 'plan') {
            updateCurrentAiMsg(m => ({ ...m, plan: data }));
          } else if (event === 'router') {
            updateCurrentAiMsg(m => ({ ...m, router: data, model: data.model || m.model }));
          } else if (event === 'rag') {
            updateCurrentAiMsg(m => ({ ...m, ragSources: data.sources || [] }));
          } else if (event === 'tool_start') {
            updateCurrentAiMsg(m => {
              const existing = m.toolCalls.filter(t => t.tool !== data.tool);
              return {
                ...m,
                toolCalls: [
                  ...existing,
                  {
                    tool: data.tool,
                    args: data.args,
                    code: data.code,
                    isRunning: true,
                    stdout: null,
                    result: null
                  }
                ]
              };
            });
          } else if (event === 'tool_output') {
            updateCurrentAiMsg(m => {
              const updated = m.toolCalls.map(tc => {
                if (tc.tool === data.tool) {
                  return {
                    ...tc,
                    isRunning: false,
                    stdout: data.stdout,
                    result: data.result
                  };
                }
                return tc;
              });
              return { ...m, toolCalls: updated };
            });
          } else if (event === 'token') {
            updateCurrentAiMsg(m => ({ ...m, text: (m.text || '') + (data.delta || '') }));
          } else if (event === 'deliverables') {
            updateCurrentAiMsg(m => ({ ...m, deliverables: data.files || [] }));
          }
        },
        // onError fallback to synchronous call
        async (err) => {
          console.warn('Falling back to synchronous agent execution due to SSE error:', err);
          try {
            const data = await runAgent(query, uploadedFile?.file_id ?? null);
            const answer = data.final_response || data.answer || 'Completed.';
            const modelName = data.selected_model || 'qwen2.5:7b-instruct';
            updateCurrentAiMsg(m => ({
              ...m,
              text: answer,
              model: modelName,
              isStreaming: false
            }));
            if (onResponse) {
              onResponse({
                routing: { model: modelName, task: data.task_type || 'general', reason: data.routing_reason || '' },
                trace: data.audit_log || [],
                sources: data.context || [],
                files: data.generated_files || []
              });
            }
          } catch (syncErr) {
            updateCurrentAiMsg(m => ({
              ...m,
              text: `⚠️ Error executing request: ${syncErr.message}`,
              isError: true,
              isStreaming: false
            }));
          }
        },
        // onDone
        (doneData) => {
          updateCurrentAiMsg(m => ({
            ...m,
            isStreaming: false,
            model: doneData.selected_model || m.model,
            deliverables: doneData.generated_files && doneData.generated_files.length > 0 ? doneData.generated_files : m.deliverables
          }));

          if (onResponse) {
            onResponse({
              routing: {
                model: doneData.selected_model || 'qwen2.5:7b-instruct',
                task: doneData.task_type || 'general',
                reason: doneData.routing_reason || ''
              },
              trace: doneData.audit_log || [],
              sources: doneData.context || [],
              files: doneData.generated_files || []
            });
          }
        }
      );
    } catch (err) {
      updateCurrentAiMsg(m => ({
        ...m,
        text: `⚠️ Execution failed: ${err.message}`,
        isError: true,
        isStreaming: false
      }));
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
                100% On-Premises Air-Gapped Multi-Model Autonomous Agent · Zero Cloud Egress
              </div>
              <div className="chips">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} className="chip" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={m.id || i} className={`msg-row ${m.role}`}>
              <div className={`msg-avatar ${m.role === 'user' ? 'av-user' : 'av-ai'}`}>
                {m.role === 'user' ? 'U' : 'VJ'}
              </div>
              <div className="msg-body">
                {/* User uploaded file badge */}
                {m.file && (
                  <div className="msg-file-attachment">
                    📎 {m.file.name} ({(m.file.size / 1024).toFixed(1)} KB)
                  </div>
                )}

                {/* AI Structured Tool & Reasoning Elements */}
                {m.role === 'ai' && (
                  <>
                    {/* Collapsible Thinking Accordion */}
                    <ThinkingAccordion
                      plan={m.plan}
                      router={m.router}
                      ragSources={m.ragSources}
                      isStreaming={m.isStreaming}
                    />

                    {/* Tool Action Pills (Python Sandbox, Word, Excel, PPTX, OCR) */}
                    {m.toolCalls && m.toolCalls.length > 0 && (
                      <div className="tool-pills-wrap">
                        {m.toolCalls.map((tc, idx) => (
                          <ToolActionPill
                            key={idx}
                            toolName={tc.tool}
                            args={tc.args}
                            result={tc.result}
                            stdout={tc.stdout}
                            code={tc.code}
                            isRunning={tc.isRunning}
                          />
                        ))}
                      </div>
                    )}
                  </>
                )}

                {/* Main Text Content Rendered via Markdown */}
                {m.role === 'user' ? (
                  <div className="msg-text">{m.text}</div>
                ) : (
                  (m.text || m.isError) && (
                    <div className={`msg-text ${m.isError ? 'error' : ''}`}>
                      <MarkdownRenderer content={m.text} />
                    </div>
                  )
                )}

                {/* Inline Deliverables Cards (Word, Excel, PPTX, Python) */}
                {m.deliverables && m.deliverables.length > 0 && (
                  <div className="deliverables-grid">
                    <div className="deliverables-grid-title">Generated Official Deliverables:</div>
                    {m.deliverables.map((f, fIdx) => (
                      <DeliverableCard key={fIdx} file={f} />
                    ))}
                  </div>
                )}

                {/* Message Meta */}
                <div className="msg-meta">
                  <span>{fmtTime(m.ts)}</span>
                  {m.model && <span className="model-pill">{m.model}</span>}
                  {m.isStreaming && <span className="streaming-badge">● streaming</span>}
                </div>
              </div>
            </div>
          ))}

          {loading && messages.length > 0 && !messages[messages.length - 1]?.text && messages[messages.length - 1]?.toolCalls?.length === 0 && (
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
              placeholder="Ask anything or request ASME calculation, PSU approval note, spreadsheet… (Shift+Enter for newline)"
              disabled={loading}
            />
            <div className="input-toolbar">
              <button className="icon-btn send-btn" onClick={() => send()} disabled={!input.trim() || loading} title="Send">
                {loading ? <div className="spinner" /> : '↑'}
              </button>
            </div>
          </div>
          <div className="input-foot">
            <span className="input-hint">
              100% Air-Gapped · Local Multi-Model Orchestration · Sandbox Verified
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
