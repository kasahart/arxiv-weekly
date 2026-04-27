export default function WeekSelector({ weeks, toDate, onToChange }) {
  if (!weeks.length) return null
  const selectStyle = {
    background: '#131720', border: '1px solid #1e293b', color: '#94a3b8',
    fontFamily: "'IBM Plex Mono',monospace", fontSize: 11,
    padding: '4px 10px', borderRadius: 2, cursor: 'pointer', outline: 'none',
  }
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ fontSize: 10, color: '#475569', letterSpacing: 1, whiteSpace: 'nowrap' }}>
        最新週:
      </span>
      <select value={toDate ?? ''} onChange={e => onToChange(e.target.value)} style={selectStyle}>
        {weeks.map(w => (
          <option key={w.date} value={w.date}>{w.date}（{w.count}件）</option>
        ))}
      </select>
    </div>
  )
}
