/** 先頭の丸数字プレフィックス（①など）を除去する */
export function stripPrefix(text) {
  return text?.replace(/^[①-⑨]\s*/, '') ?? ''
}

/** URL クエリパラメータからフィルタ状態を読み取る */
export function readUrlState(search = window.location.search) {
  const p = new URLSearchParams(search)
  return {
    toDate:            p.get('week') || null,
    fromDate:          p.get('from') || null,
    activeCat:         p.get('cat')  || 'all',
    search:            p.get('q')    || '',
    sortByCitations:   p.get('sort') === '1',
    showFavoritesOnly: p.get('fav')  === '1',
  }
}

/** フィルタ状態を URL クエリパラメータに変換する */
export function buildUrlSearch({ toDate, fromDate, activeCat, search, sortByCitations, showFavoritesOnly }) {
  const p = new URLSearchParams()
  if (toDate)              p.set('week', toDate)
  if (fromDate)            p.set('from', fromDate)
  if (activeCat !== 'all') p.set('cat',  activeCat)
  if (search)              p.set('q',    search)
  if (sortByCitations)     p.set('sort', '1')
  if (showFavoritesOnly)   p.set('fav',  '1')
  return p.toString() ? `?${p}` : ''
}
