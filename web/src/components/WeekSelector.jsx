export default function WeekSelector({ weeks, selected, onChange }) {
  if (!weeks.length) return null
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ fontSize: 10, color: '#475569', letterSpacing: 1, whiteSpace: 'nowrap' }}>
        週を選択:
      </span>
      <select
        value={selected ?? ''}
        onChange={e => onChange(e.target.value)}
        style={{
          background: '#131720', border: '1px solid #1e293b', color: '#94a3b8',
          fontFamily: "'IBM Plex Mono',monospace", fontSize: 11,
          padding: '4px 10px', borderRadius: 2, cursor: 'pointer', outline: 'none',
        }}>
        {weeks.map(w => (
          <option key={w.date} value={w.date}>
            {w.date}（{w.count} 件）
          </option>
        ))}
      </select>
    </div>
  )
}
