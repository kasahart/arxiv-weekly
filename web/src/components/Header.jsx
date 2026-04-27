export default function Header({ total, loading }) {
  return (
    <div style={{ borderBottom: '1px solid #1e293b', padding: '18px 26px 14px', background: '#0a0d14' }}>
      <div style={{ fontSize: 10, color: '#38bdf8', letterSpacing: 4, opacity: 0.7, marginBottom: 6 }}>
        ARXIV MONITOR / CS.SD - EESS.AS
      </div>
      <div style={{ fontSize: 21, fontFamily: "'Space Mono',monospace", fontWeight: 700,
        color: '#f1f5f9', letterSpacing: -0.5 }}>
        音声研究週報
        <span style={{ fontSize: 12, color: '#475569', fontWeight: 400, marginLeft: 12 }}>
          音の基盤モデル・音源分離・異音検知
        </span>
      </div>
      {!loading && total > 0 && (
        <div style={{ fontSize: 10, color: '#475569', marginTop: 4 }}>
          {total} 論文 表示中
        </div>
      )}
    </div>
  )
}
