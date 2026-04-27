import { useState, useEffect, useRef, useCallback } from 'react'
import Header from './components/Header'
import WeekSelector from './components/WeekSelector'
import CategoryFilter from './components/CategoryFilter'
import PaperCard from './components/PaperCard'
import TrendSummary from './components/TrendSummary'

const DATA_BASE = './data'
const LS_TO_DATE = 'arxiv-to-date'

async function fetchCitationsForPapers(papers) {
  const CHUNK = 10
  const results = {}
  for (let i = 0; i < papers.length; i += CHUNK) {
    const chunk = papers.slice(i, i + CHUNK)
    await Promise.allSettled(chunk.map(async p => {
      const id = p.id.split('v')[0]
      try {
        const res = await fetch(`https://api.openalex.org/works/https://doi.org/10.48550/arXiv.${id}?select=cited_by_count`)
        if (!res.ok) return
        const data = await res.json()
        if (data?.cited_by_count != null) results[id] = data.cited_by_count
      } catch {}
    }))
    if (i + CHUNK < papers.length) await new Promise(r => setTimeout(r, 300))
  }
  return results
}

async function fetchGithubReposForPapers(papers) {
  const CHUNK = 10
  const results = {}
  for (let i = 0; i < papers.length; i += CHUNK) {
    const chunk = papers.slice(i, i + CHUNK)
    await Promise.allSettled(chunk.map(async p => {
      const id = p.id.split('v')[0]
      try {
        const res = await fetch(`https://huggingface.co/api/papers/${id}`)
        if (!res.ok) return
        const data = await res.json()
        if (data?.githubRepo) results[id] = data.githubRepo
      } catch {}
    }))
    if (i + CHUNK < papers.length) await new Promise(r => setTimeout(r, 300))
  }
  return results
}

async function fetchWeekData(date) {
  const res = await fetch(`${DATA_BASE}/weekly/${date}.json`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

function enrichWeek(weekData, citationMap, githubMap) {
  return weekData
}

export default function App() {
  const [index, setIndex] = useState(null)
  const [loadedWeeks, setLoadedWeeks] = useState([])
  const [toDate, setToDate] = useState(null)
  const [fromDate, setFromDate] = useState(null)
  const [nextLoadIdx, setNextLoadIdx] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [activeCat, setActiveCat] = useState('all')
  const [citationMap, setCitationMap] = useState({})
  const [githubMap, setGithubMap] = useState({})
  const sentinelRef = useRef(null)

  // Load index and restore saved week
  useEffect(() => {
    fetch(`${DATA_BASE}/index.json`)
      .then(r => r.json())
      .then(data => {
        setIndex(data)
        const weeks = data.weeks ?? []
        const hashDate = window.location.hash.slice(1)
        const savedDate = localStorage.getItem(LS_TO_DATE)
        const startDate =
          (hashDate && weeks.find(w => w.date === hashDate) ? hashDate : null) ||
          (savedDate && weeks.find(w => w.date === savedDate) ? savedDate : null) ||
          weeks[0]?.date
        if (startDate) setToDate(startDate)
        else setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  // When toDate changes: reset and load first week
  useEffect(() => {
    if (!toDate || !index) return
    const weeks = index.weeks
    const idx = weeks.findIndex(w => w.date === toDate)
    if (idx < 0) { setLoading(false); return }

    localStorage.setItem(LS_TO_DATE, toDate)
    window.history.replaceState(null, '', `#${toDate}`)

    setLoadedWeeks([])
    setCitationMap({})
    setGithubMap({})
    setLoading(true)
    setHasMore(true)

    fetchWeekData(toDate).then(data => {
      setLoadedWeeks([data])
      setNextLoadIdx(idx + 1)
      setHasMore(idx + 1 < weeks.length)
      setLoading(false)
      const papers = data.categories.flatMap(c => c.papers)
      fetchCitationsForPapers(papers).then(m => setCitationMap(prev => ({ ...prev, ...m })))
      fetchGithubReposForPapers(papers).then(m => setGithubMap(prev => ({ ...prev, ...m })))
    }).catch(() => setLoading(false))
  }, [toDate, index])

  // Load next (older) week
  const loadNextWeek = useCallback(() => {
    if (!index || loadingMore || !hasMore) return
    const weeks = index.weeks
    if (nextLoadIdx >= weeks.length) { setHasMore(false); return }

    // 期間の下限を超えたら停止
    const nextDate = weeks[nextLoadIdx].date
    if (fromDate && nextDate < fromDate) { setHasMore(false); return }
    fetchWeekData(nextDate).then(data => {
      setLoadedWeeks(prev => [...prev, data])
      const newIdx = nextLoadIdx + 1
      setNextLoadIdx(newIdx)
      setHasMore(newIdx < weeks.length)
      setLoadingMore(false)
      const papers = data.categories.flatMap(c => c.papers)
      fetchCitationsForPapers(papers).then(m => setCitationMap(prev => ({ ...prev, ...m })))
      fetchGithubReposForPapers(papers).then(m => setGithubMap(prev => ({ ...prev, ...m })))
    }).catch(() => setLoadingMore(false))
  }, [index, nextLoadIdx, loadingMore, hasMore, fromDate])

  // IntersectionObserver: load more when sentinel is visible
  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel) return
    const observer = new IntersectionObserver(
      entries => { if (entries[0].isIntersecting) loadNextWeek() },
      { threshold: 0.1 }
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [loadNextWeek])

  // All unique categories across loaded weeks
  const allCategories = [...new Map(
    loadedWeeks.flatMap(w => w.categories).map(c => [c.id, c])
  ).values()]

  const totalPapers = loadedWeeks.reduce(
    (sum, w) => sum + w.categories.reduce((s, c) => s + c.papers.length, 0), 0
  )

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
        .ctrlBtn{background:transparent;border:1px solid #1e293b;color:#64748b;
          font-family:'IBM Plex Mono',monospace;font-size:10px;padding:5px 10px;
          cursor:pointer;letter-spacing:1px;transition:all 0.15s;border-radius:2px}
        .ctrlBtn:hover{color:#94a3b8;border-color:#334155}
        .ctrlBtn.active{border-color:#38bdf8;color:#38bdf8;background:#38bdf810}
        .fd{animation:fd 0.3s ease both}
        @keyframes fd{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
        .refLink{color:inherit;text-decoration:none;border-bottom:1px solid currentColor;
          opacity:0.85;transition:opacity 0.15s}
        .refLink:hover{opacity:1}
      `}</style>

      <Header total={totalPapers} loading={loading} />

      <div style={{ borderBottom: '1px solid #1e293b', padding: '10px 26px',
        background: '#0a0d14', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <WeekSelector
          weeks={index?.weeks ?? []}
          toDate={toDate}
          fromDate={fromDate}
          onToChange={date => { setFromDate(null); setToDate(date) }}
          onFromChange={setFromDate}
        />
        <CategoryFilter categories={allCategories} active={activeCat} onChange={setActiveCat} />
      </div>

      <div style={{ padding: '24px 26px', maxWidth: 960 }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '80px 0', color: '#38bdf8', letterSpacing: 3 }}>
            loading...
          </div>
        )}

        {loadedWeeks.map((week) => {
          const filteredCats = week.categories
            .filter(c => activeCat === 'all' || c.id === activeCat)
            .filter(c => c.papers.length > 0)

          return (
            <div key={week.date} style={{ marginBottom: 56 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
                paddingBottom: 10, borderBottom: '1px solid #1e293b' }}>
                <span style={{ fontSize: 11, color: '#38bdf8', fontWeight: 600, letterSpacing: 2 }}>
                  WEEK {week.date}
                </span>
                <span style={{ fontSize: 9, color: '#334155' }}>
                  {week.categories.reduce((s, c) => s + c.papers.length, 0)} papers
                </span>
              </div>

              <TrendSummary trend={week.trend} />

              {filteredCats.map((cat, ci) => (
                <div key={cat.id} style={{ marginBottom: 36 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                    <span style={{ fontSize: 13, color: cat.color, fontWeight: 600, letterSpacing: 2 }}>
                      {cat.label}
                    </span>
                    <div style={{ flex: 1, height: 1, background: `${cat.color}25` }} />
                    <span style={{ fontSize: 9, color: '#334155' }}>{cat.papers.length} papers</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                    {cat.papers.map((paper, pi) => {
                      const id = paper.id.split('v')[0]
                      return (
                        <PaperCard key={paper.id} paper={paper} cat={cat}
                          animDelay={ci * 0.05 + pi * 0.04}
                          citationCount={citationMap[id]}
                          githubUrl={githubMap[id]} />
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          )
        })}

        <div ref={sentinelRef} style={{ height: 1 }} />
        {loadingMore && (
          <div style={{ textAlign: 'center', padding: '24px 0', color: '#334155', fontSize: 10, letterSpacing: 2 }}>
            loading older weeks...
          </div>
        )}
        {!hasMore && loadedWeeks.length > 0 && (
          <div style={{ textAlign: 'center', padding: '24px 0', color: '#1e293b', fontSize: 9, letterSpacing: 2 }}>
            - all weeks loaded -
          </div>
        )}
        <div style={{ marginTop: 22, fontSize: 9, color: '#1e293b', letterSpacing: 1,
          borderTop: '1px solid #1e293b', paddingTop: 14 }}>
          SOURCE: arXiv cs.SD / eess.AS - POWERED BY GitHub Models (GPT-4o) - 毎週金曜更新
        </div>
      </div>
    </div>
  )
}
