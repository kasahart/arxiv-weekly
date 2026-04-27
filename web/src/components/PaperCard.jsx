import { useState } from 'react'

const SECTIONS = [
  { key: 'what',       icon: '1.', label: 'どんなもの？',        color: '#cbd5e1' },
  { key: 'novel',      icon: '2.', label: '先行研究より優れた点', color: '#38bdf8' },
  { key: 'method',     icon: '3.', label: '技術・手法のキモ',     color: '#a78bfa' },
  { key: 'validation', icon: '4.', label: '有効性の検証',         color: '#4ade80' },
  { key: 'discussion', icon: '5.', label: '議論・限界',           color: '#fb923c' },
  { key: 'nextReads',  icon: '6.', label: '次に読むべき論文',     color: '#f472b6' },
]

function stripPrefix(text) {
  return text?.replace(/^[①-⑨]\s*/, '') ?? ''
}

export default function PaperCard({ paper, cat, animDelay = 0, citationCount, githubUrl }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="fd" style={{
      background: '#111520',
      border: `1px solid ${expanded ? cat.color + '70' : cat.color + '40'}`,
      borderLeft: `4px solid ${cat.color}`,
      borderRadius: 4,
      boxShadow: expanded ? `0 0 20px rgba(0,0,0,0.3)` : 'none',
      animationDelay: `${animDelay}s`,
    }}>
      <div onClick={() => setExpanded(e => !e)}
        style={{ padding: '13px 16px 11px', cursor: 'pointer', userSelect: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 7, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, padding: '2px 10px', background: cat.color,
            color: '#080c14', fontWeight: 700, letterSpacing: 1, borderRadius: 2, flexShrink: 0 }}>
            {paper.date}
          </span>
          <span style={{ fontSize: 9, padding: '2px 8px',
            border: `1px solid ${cat.color}50`, color: cat.color, background: `${cat.color}10`, borderRadius: 2 }}>
            {cat.label}
          </span>
          <span style={{ fontSize: 10, color: '#94a3b8', fontWeight: 500 }}>{paper.org}</span>
          <span style={{ fontSize: 9, color: '#334155' }}>arXiv:{paper.id}</span>
          {githubUrl && (
            <a href={githubUrl} target="_blank" rel="noreferrer"
              onClick={e => e.stopPropagation()}
              style={{ fontSize: 9, padding: '2px 7px', textDecoration: 'none',
                border: '1px solid #4ade8060', color: '#4ade80',
                background: '#4ade8010', borderRadius: 2, fontWeight: 600 }}>
              Code
            </a>
          )}
          {citationCount != null && citationCount > 0 && (
            <span style={{ fontSize: 9, padding: '2px 7px',
              border: '1px solid #475569', color: '#94a3b8', borderRadius: 2 }}>
              cited {citationCount}
            </span>
          )}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
            <a href={paper.url} target="_blank" rel="noreferrer"
              onClick={e => e.stopPropagation()}
              style={{ fontSize: 9, color: '#475569', textDecoration: 'none' }}>
              arXiv
            </a>
            <span style={{ fontSize: 12, color: expanded ? cat.color : '#334155',
              transition: 'color 0.15s' }}>
              {expanded ? '▴' : '▾'}
            </span>
          </div>
        </div>
        <div style={{ fontSize: 13, color: '#e2e8f0', lineHeight: 1.6, fontWeight: 500 }}>
          {paper.title}
        </div>
        <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.6, marginTop: 3 }}>
          {paper.titleJa}
        </div>
        {!expanded && paper.what && (
          <div style={{ fontSize: 11, color: '#64748b', lineHeight: 1.8, marginTop: 8,
            paddingLeft: 8, borderLeft: '2px solid #1e293b' }}>
            {stripPrefix(paper.what)}
          </div>
        )}
      </div>

      {expanded && (
        <div style={{ borderTop: `1px solid ${cat.color}18`, animation: 'fd 0.2s ease both' }}>
          {SECTIONS.map((sm, si) => (
            <div key={sm.key} style={{
              borderTop: si === 0 ? 'none' : `1px solid ${cat.color}10`,
              padding: '11px 18px',
            }}>
              <div style={{ fontSize: 9, color: sm.color, fontWeight: 600,
                letterSpacing: 1.5, marginBottom: 6 }}>
                {sm.icon} {sm.label}
              </div>
              {sm.key === 'nextReads' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {(paper.nextReads ?? []).map((r, i) => (
                    <div key={i} style={{ fontSize: 11, lineHeight: 1.7 }}>
                      <span style={{ color: sm.color, marginRight: 5, opacity: 0.6 }}>-</span>
                      {r.url ? (
                        <a href={r.url} target="_blank" rel="noreferrer"
                          className="refLink" style={{ color: sm.color }}>
                          {r.label}
                        </a>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>{r.label}</span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 11, color: '#cbd5e1', lineHeight: 1.9,
                  paddingLeft: 8, borderLeft: `2px solid ${sm.color}40` }}>
                  {stripPrefix(paper[sm.key])}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
