
import { useEffect, useState } from 'react';
import { getFiles, downloadFile } from '../services/api';

const EXT_ICON  = { docx:'📝', xlsx:'📊', pptx:'📑', pdf:'📄', txt:'📃', py:'🐍', png:'🖼️', jpg:'🖼️', jpeg:'🖼️', webp:'🖼️', json:'📋', csv:'📊' };
const EXT_COLOR = { docx:'var(--blue-dim)', xlsx:'var(--green-dim)', pptx:'var(--amber-dim)', pdf:'var(--red-dim)', py:'var(--cyan-dim)' };

function fmtSize(b) {
  if (!b) return '';
  if (b > 1e6) return (b/1e6).toFixed(1)+' MB';
  if (b > 1e3) return (b/1e3).toFixed(0)+' KB';
  return b+' B';
}

export default function GeneratedFiles({ newFiles }) {
  const [files,   setFiles]   = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchFileList = () => {
    getFiles()
      .then(r => setFiles(Array.isArray(r) ? r : []))
      .catch(() => setFiles([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchFileList();
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
    return <div style={{ display:'flex', gap:7, alignItems:'center', color:'var(--text-muted)', fontSize:'.78rem' }}><div className="spinner" /> Loading workspace files…</div>;
  }

  if (files.length === 0) {
    return <div style={{ fontSize:'.8rem', color:'var(--text-muted)', textAlign:'center', padding:'20px 0' }}>No workspace files found</div>;
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
        <div className="card-head">{files.length} Workspace File{files.length !== 1 ? 's' : ''}</div>
        <button 
          onClick={fetchFileList} 
          style={{ background:'none', border:'none', color:'var(--text-muted)', cursor:'pointer', fontSize:'.75rem' }}
          title="Refresh file list"
        >
          🔄 Refresh
        </button>
      </div>
      {files.map((f, i) => {
        const ext = (f.type || f.name?.split('.').pop() || '').toLowerCase();
        const displayName = f.clean_name || f.name;
        return (
          <div key={i} className="file-row fade-in" style={{ animationDelay:`${i*.03}s` }}>
            <div className="file-icon" style={{ background: EXT_COLOR[ext] || 'var(--bg-elevated)' }}>
              {EXT_ICON[ext] || '📁'}
            </div>
            <div className="file-info" style={{ overflow:'hidden' }}>
              <div className="file-name" title={f.name} style={{ textOverflow:'ellipsis', overflow:'hidden', whiteSpace:'nowrap' }}>
                {displayName}
              </div>
              <div className="file-meta" style={{ display:'flex', gap:6, alignItems:'center' }}>
                <span>{ext.toUpperCase()} {fmtSize(f.size)}</span>
                {f.category && (
                  <span style={{ 
                    fontSize:'.65rem', 
                    background:'rgba(255,255,255,0.06)', 
                    padding:'1px 5px', 
                    borderRadius:4, 
                    color:'var(--text-muted)' 
                  }}>
                    {f.category}
                  </span>
                )}
              </div>
            </div>
            <button
              className="icon-btn"
              title={`Download ${displayName}`}
              style={{ fontSize: 14, color: 'var(--text-secondary)' }}
              onClick={() => downloadFile(f.name).catch(console.error)}
            >⤓</button>
          </div>
        );
      })}
    </div>
  );
}
