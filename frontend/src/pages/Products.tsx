import { useEffect, useMemo, useState } from 'react'
import type { CSSProperties } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fetchCategories, fetchProducts } from '../api'
import { useChatResults } from '../chatResults'
import ProductCard from '../components/ProductCard'
import type { Category, Product } from '../types'

const SORTS = {
  featured: { label: 'Featured', fn: (a: Product, b: Product) => a.name.localeCompare(b.name) },
  'price-asc': { label: 'Price: low to high', fn: (a: Product, b: Product) => a.price - b.price || a.name.localeCompare(b.name) },
  'price-desc': { label: 'Price: high to low', fn: (a: Product, b: Product) => b.price - a.price || a.name.localeCompare(b.name) },
  stock: { label: 'Most in stock', fn: (a: Product, b: Product) => (b.total_stock ?? 0) - (a.total_stock ?? 0) },
} as const
type SortKey = keyof typeof SORTS

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [params, setParams] = useSearchParams()
  const { results: chatResults, version, clear } = useChatResults()

  // Category and sort live in the URL (/products?category=hoodies&sort=price-asc): shareable and Back-button friendly.
  const category = params.get('category')
  const sort = (params.get('sort') as SortKey) in SORTS ? (params.get('sort') as SortKey) : 'featured'
  const activeCategory = categories.find((c) => c.slug === category)

  useEffect(() => {
    Promise.all([fetchProducts(), fetchCategories()])
      .then(([p, c]) => {
        setProducts(p)
        setCategories(c)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // Picking an aisle from the nav or footer (?category=…) means the shopper is browsing again.
  useEffect(() => {
    if (category) clear()
  }, [category, clear])

  // New results from the chat: bring them into view.
  useEffect(() => {
    if (chatResults) window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [chatResults, version])

  function setParam(key: string, value: string | null) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next)
  }

  function pickCategory(slug: string | null) {
    clear() // leaving chat results for a browse view
    setParam('category', slug)
  }

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase()
    return products
      .filter((p) => !category || p.category === category)
      .filter(
        (p) =>
          !q ||
          [p.name, p.garment_type, p.description, ...p.colors, ...p.search_tags].join(' ').toLowerCase().includes(q),
      )
      .sort(SORTS[sort].fn)
  }, [products, query, category, sort])

  // Chat cards come from the API without live stock; enrich them from the cached catalogue.
  const byId = useMemo(() => new Map(products.map((p) => [p.product_id, p])), [products])

  const tabs = (
    <div className="cat-tabs" role="tablist" aria-label="Apparel type">
      <button
        role="tab"
        aria-selected={!category && !chatResults}
        className={`cat-tab ${!category && !chatResults ? 'active' : ''}`}
        onClick={() => pickCategory(null)}
      >
        All <span className="cat-count">{products.length}</span>
      </button>
      {categories.map((c) => (
        <button
          key={c.slug}
          role="tab"
          aria-selected={category === c.slug && !chatResults}
          className={`cat-tab ${category === c.slug && !chatResults ? 'active' : ''}`}
          onClick={() => pickCategory(c.slug)}
        >
          {c.label} <span className="cat-count">{c.count}</span>
        </button>
      ))}
    </div>
  )

  if (chatResults) {
    return (
      <div className="page">
        {tabs}
        <section className="chat-results" aria-live="polite">
          <div className="section-head">
            <div>
              <span className="eyebrow">
                <span className="spark">✦</span> From your chat
              </span>
              <h1>{chatResults.title}</h1>
              <p className="muted count">
                {chatResults.total} {chatResults.total === 1 ? 'match' : 'matches'} found by the assistant. Tap a
                card for sizes and details.
              </p>
            </div>
            <button className="btn btn-ghost" onClick={clear}>
              Show all {products.length || ''} products
            </button>
          </div>
          <div className="grid" key={version}>
            {chatResults.products.map((p, i) => (
              <ProductCard
                key={p.product_id}
                product={byId.get(p.product_id) ?? p}
                className="card-enter"
                style={{ '--i': Math.min(i, 15) } as CSSProperties}
              />
            ))}
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="page">
      <nav className="crumbs" aria-label="Breadcrumb">
        <Link to="/">Home</Link>
        <span>/</span>
        {activeCategory ? (
          <>
            <Link to="/products" onClick={() => clear()}>
              Shop
            </Link>
            <span>/</span>
            <span aria-current="page">{activeCategory.label}</span>
          </>
        ) : (
          <span aria-current="page">Shop</span>
        )}
      </nav>

      <div className="section-head">
        <div>
          <span className="eyebrow">{activeCategory ? 'Shop by apparel' : 'The collection'}</span>
          <h1>{activeCategory?.label ?? 'All products'}</h1>
        </div>
        <div className="shop-controls">
          <input
            className="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search colleges, teams, colors…"
            aria-label="Search products"
          />
          <select
            className="sort"
            value={sort}
            onChange={(e) => setParam('sort', e.target.value === 'featured' ? null : e.target.value)}
            aria-label="Sort products"
          >
            {Object.entries(SORTS).map(([key, s]) => (
              <option key={key} value={key}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {tabs}

      {loading && <p className="muted">Loading the catalogue…</p>}
      {error && <p className="error">Couldn't load products ({error}). Is the backend running on port 8000?</p>}
      {!loading && !error && (
        <p className="muted count">
          {visible.length} {visible.length === 1 ? 'style' : 'styles'}
          {activeCategory ? ` in ${activeCategory.label}` : ''} · or ask the assistant to find something for you
        </p>
      )}

      <div className="grid" key={`${category}-${sort}`}>
        {visible.map((p, i) => (
          <ProductCard
            key={p.product_id}
            product={p}
            className="card-enter"
            style={{ '--i': Math.min(i, 12) } as CSSProperties}
          />
        ))}
      </div>
      {!loading && !error && visible.length === 0 && (
        <p className="muted">No styles match “{query}”. Try another word, or ask the assistant.</p>
      )}
    </div>
  )
}
