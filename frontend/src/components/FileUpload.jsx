
import { useRef, useState } from 'react';
import { uploadFile } from '../services/api';

const ACCEPT = '.pdf,.docx,.xlsx,.png,.jpg,.jpeg,.webp,.txt,.py';

function fileIcon(name = '') {
  if (/\.pdf$/i.test(name))  return '📄';
  if (/\.docx$/i.test(name)) return '📝';
  if (/\.xlsx$/i.test(name)) return '📊';
  if (/\.(png|jpg|jpeg|webp)/i.test(name)) return '🖼';
  return '📁';
}
function fmtSize(b) {
  if (b > 1e6) return (b/1e6).toFixed(1)+' MB';
  if (b > 1e3) return (b/1e3).toFixed(0)+' KB';
  return b+' B';
}

export default function FileUpload({ onUpload, compact }) {
  const [dragging, setDragging]   = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded,  setUploaded]  = useState(null);
  const [error,     setError]     = useState('');
  const inputRef = useRef(null);

  async function process(file) {
    setError('');
    setUploading(true);
    try {
      const res = await uploadFile(file);
      const obj = { ...res, name: file.name, size: file.size };
      setUploaded(obj);
      onUpload?.(obj);
    } catch (e) { setError(e.message); }
    finally     { setUploading(false); }
  }

  if (compact) {
    // Compact version for sidebar
    return (
      <div>
        {uploaded ? (
          <div className="file-row">
            <div className="file-icon" style={{ background: 'var(--blue-dim)' }}>{fileIcon(uploaded.name)}</div>
            <div className="file-info">
              <div className="file-name">{uploaded.name}</div>
              <div className="file-meta">{fmtSize(uploaded.size)}</div>
            </div>
            <button className="icon-btn" onClick={() => { setUploaded(null); onUpload?.(null); }} style={{ fontSize: 11, color: 'var(--text-muted)' }}>✕</button>
          </div>
        ) : (
          <button
            className="btn btn-ghost btn-full btn-sm"
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? <><div className="spinner" /> Uploading…</> : <>📎 Attach file</>}
          </button>
        )}
        <input ref={inputRef} type="file" accept={ACCEPT} style={{ display: 'none' }}
          onChange={e => { const f = e.target.files?.[0]; if (f) process(f); }} />
        {error && <div style={{ fontSize: '.7rem', color: 'var(--red)', marginTop: 6 }}>{error}</div>}
      </div>
    );
  }

  return (
    <div>
      <div
        className={`drop-zone${dragging ? ' drag' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) process(f); }}
        onClick={() => inputRef.current?.click()}
      >
        <div className="drop-zone-icon">{uploading ? '⏳' : '📂'}</div>
        <div className="drop-zone-label">{uploading ? 'Uploading…' : 'Click or drag a file'}</div>
        <div className="drop-zone-sub">PDF · DOCX · XLSX · PNG/JPG · TXT · PY</div>
      </div>
      <input ref={inputRef} type="file" accept={ACCEPT} style={{ display: 'none' }}
        onChange={e => { const f = e.target.files?.[0]; if (f) process(f); }} />
      {uploaded && (
        <div className="file-row fade-in" style={{ marginTop: 8 }}>
          <div className="file-icon" style={{ background: 'var(--blue-dim)' }}>{fileIcon(uploaded.name)}</div>
          <div className="file-info">
            <div className="file-name">{uploaded.name}</div>
            <div className="file-meta">{fmtSize(uploaded.size)}</div>
          </div>
          <span className="badge b-green">Uploaded</span>
        </div>
      )}
      {error && <div style={{ fontSize: '.73rem', color: 'var(--red)', marginTop: 6 }}>⚠ {error}</div>}
    </div>
  );
}
