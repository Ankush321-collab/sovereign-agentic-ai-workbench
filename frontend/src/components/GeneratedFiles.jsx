
import { useEffect, useState } from 'react';
import { getFiles, downloadFile } from '../services/api';

const EXT_ICON  = { docx:'📝', xlsx:'📊', pptx:'📑', pdf:'📄', txt:'📃', py:'🐍' };
const EXT_COLOR = { docx:'var(--blue-dim)', xlsx:'var(--green-dim)', pptx:'var(--amber-dim)', pdf:'var(--red-dim)' };

function fmtSize(b) {
  if (!b) return '';
  if (b > 1e6) return (b/1e6).toFixed(1)+' MB';
  if (b > 1e3) return (b/1e3).toFixed(0)+' KB';
  return b+' B';
}

export default function GeneratedFiles({ newFiles }) {
  const [files,   setFiles]   = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getFiles()
      .then(r => setFiles(Array.isArray(r) ? r : []))
      .catch(() => setFiles([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (newFiles?.length > 0) {
      setFiles(prev => {
        const names = new Set(prev.map(f => f.name));
        return [...prev, ...newFiles.filter(f => !names.has(f.name))];
      });
    }
  }, [newFiles]);

  if (loading) {
    return <div style={{ display:'flex', gap:7, alignItems:'center', color:'var(--text-muted)', fontSize:'.78rem' }}><div className="spinner" /> Loading files…</div>;
  }

  if (files.length === 0) {
    return <div style={{ fontSize:'.8rem', color:'var(--text-muted)', textAlign:'center', padding:'20px 0' }}>No files generated yet</div>;
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
      <div className="card-head">{files.length} File{files.length !== 1 ? 's' : ''}</div>
      {files.map((f, i) => {
        const ext = (f.type || f.name?.split('.').pop() || '').toLowerCase();
        return (
          <div key={i} className="file-row fade-in" style={{ animationDelay:`${i*.04}s` }}>
            <div className="file-icon" style={{ background: EXT_COLOR[ext] || 'var(--bg-elevated)' }}>
              {EXT_ICON[ext] || '📁'}
            </div>
            <div className="file-info">
              <div className="file-name">{f.name}</div>
              <div className="file-meta">{ext.toUpperCase()} {fmtSize(f.size)}</div>
            </div>
            <button
              className="icon-btn"
              title="Download"
              style={{ fontSize: 14, color: 'var(--text-secondary)' }}
              onClick={() => downloadFile(f.name).catch(console.error)}
            >⤓</button>
          </div>
        );
      })}
    </div>
  );
}
