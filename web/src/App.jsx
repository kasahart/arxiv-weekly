import { useState, useEffect } from 'react'
import Header from './components/Header'
import WeekSelector from './components/WeekSelector'
import CategoryFilter from './components/CategoryFilter'
import PaperCard from './components/PaperCard'
import TrendSummary from './components/TrendSummary'

const DATA_BASE = './data'

async function fetchAllCitationCounts(papers) {
  const CHUNK = 10
  const results = {}

  for (let i = 0; i < papers.length; i += CHUNK) {
    const chunk = papers.slice(i, i + CHUNK)
    await Promise.allSettled(
      chunk.map(async p => {
        const id = p.id.split('v')[0]
        try {
          const res = await fetch(
            `https://api.semanticscholar.org/graph/v1/paper/arXiv:${id}?fields=citationCount`
          )
          if (!res.ok) return
          const data = await res.json()
          if (data?.citationCount != null) results[id] = data.citationCount
        } catch {}
      })
    )
    // チャンク間で少し待機してレート制限を回避
    if (i + CHUNK < papers.length) await new Promise(r => setTimeout(r, 500))
  }
  return results
}

export default function App() {
  const [index, setIndex] = useState(null)
  const [weekData, setWeekData] = useState(null)
  const [selectedDate, setSelectedDate] = useState(null)
  const [activeCat, setActiveCat] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [citationMap, setCitationMap] = useState({})

  // インデックス取得
  useEffect(() => {
    fetch(`${DATA_BASE}/index.json`)
      .then(r => r.json())
      .then(data => {
        setIndex(data)
        if (data.weeks?.length > 0) setSelectedDate(data.weeks[0].date)
      })
      .catch(() => setSelectedDate('latest'))
  }, [])

  // 週データ取得
  useEffect(() => {
    if (!selectedDate) return
    setLoading(true)
    setError(null)
    setActiveCat('all')
    setCitationMap({})

    const url = selectedDate === 'latest'
      ? `${DATA_BASE}/latest.json`
      : `${DATA_BASE}/weekly/${selectedDate}.json`

    fetch(url)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(data => { setWeekData(data); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [selectedDate])

  // 週データロード後に被引用数を非同期取得（表示をブロックしない）
  useEffect(() => {
    if (!weekData) return
    const allPapers = weekData.categories.flatMap(c => c.papers)
    if (allPapers.length === 0) return
    fetchAllCitationCounts(allPapers).then(map => setCitationMap(map))
  }, [weekData])

  const categories = weekData?.categories ?? []
  const filtered = activeCat === 'all'
    ? categories
    : categories.filter(c => c.id === activeCat)

  const totalPapers = categories.reduce((a, c) => a + c.papers.length, 0)

  return (
    <div style={{ minHeight: '100vh', background: '#0f1117', color: '#e2e8f0',
      fontFamily: "'IBM Plex Mono','Courier New',monospace" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Mono:wght@700&display=swap');
        *{box-sizing:border-box;margin:0;padding:0}
        ::-webkit-scrollbar{width:4px}
        ::-webkit-scrollbar-thumb{background:#38bdf8;border-radius:2px}
        .catBtn{background:transparent;border:1px solid #1e293b;color:#64748b;
          font-family:'IBM Plex Mono',monospace;font-size:10px;padding:5px 13px;
          cursor:pointer;letter-spacing:1px;transition:all 0.15s;border-radius:2px;white-space:nowrap}
        .catBtn:hover{color:#94a3b8;border-color:#334155}
        .fd{animation:fd 0.3s ease both}
        @keyframes fd{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
        .refLink{color:inherit;text-decoration:none;border-bottom:1px solid currentColor;
          opacity:0.85;transition:opacity 0.15s}
        .refLink:hover{opacity:1}
      `}</style>

      <Header date={weekData?.date} total={totalPapers} loading={loading} />

      <div style={{ borderBottom: '1px solid #1e293b', padding: '10px 26px',
        background: '#0a0d14', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <WeekSelector weeks={index?.weeks ?? []} selected={selectedDate} onChange={setSelectedDate} />
        <CategoryFilter categories={categories} active={activeCat} onChange={setActiveCat} />
      </div>

      <div style={{ padding: '24px 26px', maxWidth: 960 }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '80px 0', color: '#38bdf8', letterSpacing: 3 }}>
            ▸ 論文データを読み込み中...
          </div>
        )}
        {error && (
          <div style={{ border: '1px solid #ef4444', padding: '16px 20px', color: '#fca5a5', fontSize: 12 }}>
            ✕ データの読み込みに失敗しました: {error}
          </div>
        )}
        {!loading && !error && filtered.map((cat, ci) => (
          <div key={cat.id} style={{ marginBottom: 36 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
              <span style={{ fontSize: 13, color: cat.color, fontWeight: 600, letterSpacing: 2 }}>
                {cat.label}
              </span>
              <div style={{ flex: 1, height: 1, background: `${cat.color}25` }} />
              <span style={{ fontSize: 9, color: '#334155' }}>{cat.papers.length} papers</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {cat.papers.map((paper, pi) => (
                <PaperCard key={paper.id} paper={paper} cat={cat}
                  animDelay={ci * 0.05 + pi * 0.04}
                  citationCount={citationMap[paper.id.split('v')[0]]} />
              ))}
            </div>
          </div>
        ))}
        {!loading && !error && weekData && <TrendSummary trend={weekData.trend} />}
        <div style={{ marginTop: 22, fontSize: 9, color: '#1e293b', letterSpacing: 1,
          borderTop: '1px solid #1e293b', paddingTop: 14 }}>
          ◦ SOURCE: arXiv cs.SD · eess.AS ◦ POWERED BY GitHub Models (GPT-4o) ◦ 毎週金曜更新
        </div>
      </div>
    </div>
  )
}
