export default function TrendSummary({ trend = [] }) {
  return (
    <div style={{ border: '1px solid #1a3020', background: '#0d1812', padding: '18px 22px',
      borderLeft: '4px solid #4ade80', borderRadius: 4, marginBottom: 24 }}>
      <div style={{ fontSize: 9, color: '#4ade80', letterSpacing: 3, marginBottom: 11, fontWeight: 600 }}>
        ◈ 今週の技術トレンド（3行まとめ）
      </div>
      {trend.map((line, i) => (
        <div key={i} style={{ fontSize: 12, color: '#94a3b8', lineHeight: 2 }}>{line}</div>
      ))}
    </div>
  )
}
