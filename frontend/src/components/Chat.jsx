/**
 * components/Chat.jsx
 * Owner: Roshan
 * Chat interface — send messages, optionally attach files, see AI responses.
 */

import { useState, useRef, useEffect } from 'react';
import { sendChat } from '../services/api';

const WELCOME_MESSAGE = {
  id: 0,
  role: 'assistant',
  content:
    'Welcome to Sovereign AI Workbench. All processing happens locally — no data leaves your environment. Upload a document or type a question to begin.',
  model: null,
  timestamp: new Date(),
};

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div
      className="fade-in"
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '0.75rem',
      }}
    >
      {!isUser && (
        <div style={{
          width: 28, height: 28, borderRadius: '50%',
          background: 'linear-gradient(135deg,#3b82f6,#06b6d4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.75rem', fontWeight: 700, flexShrink: 0,
          marginRight: '0.5rem', marginTop: 2,
        }}>
          AI
        </div>
      )}
      <div style={{
        maxWidth: '80%',
        padding: '0.65rem 1rem',
        borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
        background: isUser
          ? 'linear-gradient(135deg,#3b82f6,#2563eb)'
          : 'var(--bg-card)',
        border: isUser ? 'none' : '1px solid var(--border)',
        fontSize: '0.875rem',
        lineHeight: 1.6,
        color: isUser ? '#fff' : 'var(--text-primary)',
      }}>
        {msg.file && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6,
            marginBottom: 6, padding: '4px 8px',
            background: 'rgba(255,255,255,0.08)',
            borderRadius: 6, fontSize: '0.75rem', color: '#94a3b8',
          }}>
            <span>📎</span> {msg.file}
          </div>
        )}
        <span>{msg.content}</span>
        {msg.model && (
          <div style={{ marginTop: 6, fontSize: '0.7rem', color: '#475569' }}>
            {msg.model}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '0.75rem' }}>
      <div style={{
        width: 28, height: 28, borderRadius: '50%',
        background: 'linear-gradient(135deg,#3b82f6,#06b6d4)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.75rem', fontWeight: 700,
      }}>AI</div>
      <div style={{
        padding: '0.65rem 1rem', borderRadius: '16px 16px 16px 4px',
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        display: 'flex', gap: 4, alignItems: 'center',
      }}>
        {[0, 0.2, 0.4].map((delay, i) => (
          <div key={i} style={{
            width: 6, height: 6, borderRadius: '50%',
            background: 'var(--accent-cyan)',
            animation: `pulse-dot 1.2s ease-in-out ${delay}s infinite`,
          }} />
        ))}
      </div>
    </div>
  );
}

export default function Chat({ onResponse, uploadedFile }) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput]       = useState('');
  const [loading, setLoading]   = useState(false);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: text,
      file: uploadedFile?.name || null,
      timestamp: new Date(),
    };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await sendChat(text, uploadedFile?.id || null);
      const aiMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        model: data.model,
        timestamp: new Date(),
      };
      setMessages((m) => [...m, aiMsg]);
      if (onResponse) onResponse(data);
    } catch (err) {
      setMessages((m) => [...m, {
        id: Date.now() + 1, role: 'assistant',
        content: `Error: ${err.message}. Make sure the backend is running.`,
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: 'var(--accent-green)',
          }} className="pulse" />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            CHAT — LOCAL AI
          </span>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
        {messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '0.75rem', borderTop: '1px solid var(--border)' }}>
        {uploadedFile && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6,
            marginBottom: 6, padding: '4px 10px',
            background: 'rgba(59,130,246,0.1)', borderRadius: 6,
            fontSize: '0.75rem', color: 'var(--accent-blue)',
            border: '1px solid rgba(59,130,246,0.2)',
          }}>
            <span>📎</span> {uploadedFile.name}
          </div>
        )}
        <div style={{ display: 'flex', gap: 8 }}>
          <textarea
            ref={textareaRef}
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything... (Enter to send, Shift+Enter for newline)"
            rows={2}
            style={{
              flex: 1,
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)',
              padding: '0.6rem 0.8rem',
              fontSize: '0.875rem',
              resize: 'none',
              outline: 'none',
              fontFamily: 'inherit',
              lineHeight: 1.5,
            }}
          />
          <button
            id="chat-send-btn"
            className="btn btn-primary"
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{ alignSelf: 'flex-end', minWidth: 72 }}
          >
            {loading ? <div className="spinner" /> : '↑ Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
