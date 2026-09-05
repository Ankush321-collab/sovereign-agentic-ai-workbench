
export default function Sources({ sources }) {
  if (!sources || sources.length === 0) {
    return (
      <div style={{ fontSize: '.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
        No RAG sources retrieved yet
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div className="card-head">{sources.length} Source{sources.length !== 1 ? 's' : ''}</div>
      {sources.map((s, i) => {
        const score = s.score ?? s.relevance ?? 0;
        const color = score > 0.8 ? 'var(--green)' : score > 0.6 ? 'var(--amber)' : 'var(--red)';
        return (
          <div key={i} className="src-card fade-in" style={{ animationDelay: `${i * 0.04}s` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
              <div className="src-name">📄 {s.source || s.file || 'document'}</div>
              {s.page && <span style={{ fontSize: '.64rem', color: 'var(--text-muted)', flexShrink: 0 }}>p.{s.page}</span>}
            </div>
            {s.content && <div className="src-txt">{s.content}</div>}
            <div className="score-track">
              <div className="score-fill" style={{ width: `${score * 100}%`, background: color }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
              <span style={{ fontSize: '.63rem', color: color, fontWeight: 600 }}>
                {(score * 100).toFixed(0)}% match
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
