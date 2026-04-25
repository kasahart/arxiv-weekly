export default function CategoryFilter({ categories, active, onChange }) {
  const all = [{ id: 'all', label: 'すべて', color: '#64748b', papers: [] }, ...categories]
  return (
    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
      {all.map(cat => (
        <button key={cat.id} className="catBtn"
          style={active === cat.id ? { borderColor: cat.color, color: cat.color, background: `${cat.color}10` } : {}}
          onClick={() => onChange(cat.id)}>
          {cat.label}
          {cat.id !== 'all' && (
            <span style={{ marginLeft: 5, opacity: 0.4 }}>{cat.papers.length}</span>
          )}
        </button>
      ))}
    </div>
  )
}
