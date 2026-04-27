export default function WeekSelector({ weeks, toDate, fromDate, onToChange, onFromChange }) {
  if (!weeks.length) return null
  const selectStyle = {
    background: '#131720', border: '1px solid #1e293b', color: '#94a3b8',
    fontFamily: "'IBM Plex Mono',monospace", fontSize: 13,
    padding: '4px 10px', borderRadius: 2, cursor: 'pointer', outline: 'none',
  }
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
      <span style={{ fontSize: 12, color: '#475569', letterSpacing: 1, whiteSpace: 'nowrap' }}>
        期間:
      </span>
      <select
        value={fromDate ?? ''}
        onChange={e => onFromChange(e.target.value || null)}
        style={selectStyle}
      >
        <option value="">全期間</option>
        {[...weeks].reverse().filter(w => !toDate || w.date <= toDate).map(w => (
          <option key={w.date} value={w.date}>{w.date}</option>
        ))}
      </select>
      <span style={{ fontSize: 12, color: '#334155' }}>〜</span>
      <select
        value={toDate ?? ''}
        onChange={e => onToChange(e.target.value)}
        style={selectStyle}
      >
        {weeks.filter(w => !fromDate || w.date >= fromDate).map(w => (
          <option key={w.date} value={w.date}>{w.date}（{w.count}件）</option>
        ))}
      </select>
    </div>
  )
}
