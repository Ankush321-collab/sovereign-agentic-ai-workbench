/**
 * components/Sources.jsx
 * Owner: Roshan
 * Shows RAG source citations returned from Krishna's knowledge base.
 */

export default function Sources({ sources }) {
  if (!sources || sources.length === 0) {
    return (
      <div>
        <p className="section-label">RAG Sources</p>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          No sources retrieved yet.
        </div>
      </div>
    );
  }

  return (
    <div>
      <p className="section-label">RAG Sources ({sources.length})</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {sources.map((src, i) => (
          <div
            key={i}
            className="fade-in"
            style={{
              padding: '0.6rem 0.75rem',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              animationDelay: `${i * 0.05}s`,
              animationFillMode: 'both',
            }}
          >
            {/* File + page */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ fontSize: '0.8rem' }}>📄</span>
                <span style={{
                  fontSize: '0.72rem', fontWeight: 600,
                  color: 'var(--accent-cyan)',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  maxWidth: 120,
                }}>
                  {src.source}
                </span>
                {src.page && (
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                    p.{src.page}
                  </span>
                )}
              </div>
              {/* Score bar */}
              {src.score !== undefined && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <div style={{
                    width: 36, height: 4, background: 'var(--border)', borderRadius: 2,
                  }}>
                    <div style={{
                      height: '100%', width: `${src.score * 100}%`,
                      background: src.score > 0.8
                        ? 'var(--accent-green)'
                        : src.score > 0.6
                        ? 'var(--accent-amber)'
                        : 'var(--accent-red)',
                      borderRadius: 2,
                    }} />
                  </div>
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                    {(src.score * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </div>

            {/* Excerpt */}
            <div style={{
              fontSize: '0.72rem', color: 'var(--text-secondary)',
              lineHeight: 1.5,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {src.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
