/**
 * components/FileUpload.jsx
 * Owner: Roshan
 * Drag-and-drop or click-to-upload file panel.
 */

import { useState, useRef } from 'react';
import { uploadFile } from '../services/api';

const ACCEPTED_TYPES = '.pdf,.png,.jpg,.jpeg,.webp,.docx,.xlsx,.txt';

export default function FileUpload({ onUpload }) {
  const [dragging, setDragging]   = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded]   = useState(null);
  const [error, setError]         = useState(null);
  const inputRef = useRef(null);

  async function processFile(file) {
    setError(null);
    setUploading(true);
    try {
      const result = await uploadFile(file);
      const fileObj = { ...result, name: file.name, size: file.size };
      setUploaded(fileObj);
      if (onUpload) onUpload(fileObj);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }

  function onFileChange(e) {
    const file = e.target.files[0];
    if (file) processFile(file);
  }

  function getFileIcon(name = '') {
    if (name.endsWith('.pdf'))  return '📄';
    if (name.endsWith('.docx')) return '📝';
    if (name.endsWith('.xlsx')) return '📊';
    if (name.match(/\.(png|jpg|jpeg|webp)$/i)) return '🖼️';
    return '📁';
  }

  function formatSize(bytes) {
    if (bytes > 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
    if (bytes > 1_000) return `${(bytes / 1_000).toFixed(0)} KB`;
    return `${bytes} B`;
  }

  return (
    <div>
      <p className="section-label">File Upload</p>

      {/* Drop Zone */}
      <div
        id="file-drop-zone"
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `2px dashed ${dragging ? 'var(--accent-blue)' : 'var(--border)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '1.5rem 1rem',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragging ? 'rgba(59,130,246,0.05)' : 'transparent',
          transition: 'var(--transition)',
        }}
      >
        <input
          ref={inputRef}
          id="file-input"
          type="file"
          accept={ACCEPTED_TYPES}
          style={{ display: 'none' }}
          onChange={onFileChange}
        />
        {uploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
            <div className="spinner" style={{ width: 24, height: 24 }} />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Uploading…</span>
          </div>
        ) : (
          <>
            <div style={{ fontSize: '2rem', marginBottom: 8 }}>📂</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Drop a file here or click to browse
              <br />
              <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                PDF, PNG, JPG, WEBP, DOCX, XLSX, TXT
              </span>
            </div>
          </>
        )}
      </div>

      {/* Uploaded file info */}
      {uploaded && !error && (
        <div className="fade-in" style={{
          marginTop: '0.75rem',
          padding: '0.6rem 0.75rem',
          background: 'rgba(16,185,129,0.08)',
          border: '1px solid rgba(16,185,129,0.25)',
          borderRadius: 'var(--radius-md)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span>{getFileIcon(uploaded.name)}</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{
              fontSize: '0.8rem', fontWeight: 500,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {uploaded.name}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {formatSize(uploaded.size)} · Ready
            </div>
          </div>
          <span className="badge badge-green">✓</span>
        </div>
      )}

      {error && (
        <div style={{
          marginTop: '0.5rem', fontSize: '0.75rem',
          color: 'var(--accent-red)', padding: '0.4rem 0.6rem',
          background: 'rgba(239,68,68,0.08)', borderRadius: 6,
        }}>
          {error}
        </div>
      )}

      {/* Change file button */}
      {uploaded && (
        <button
          id="change-file-btn"
          className="btn btn-secondary"
          onClick={() => { setUploaded(null); inputRef.current?.click(); }}
          style={{ marginTop: '0.5rem', width: '100%', justifyContent: 'center', fontSize: '0.75rem' }}
        >
          Change file
        </button>
      )}
    </div>
  );
}
