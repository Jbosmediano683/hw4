import { useEffect, useState } from 'react'
import type { MouseEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchCategories, fetchProduct, fetchProducts, formatPrice } from '../api'
import { useChatUI } from '../chatUI'
import ProductCard from '../components/ProductCard'
import Crest from '../components/Crest'
import { uniqueSwatches } from '../swatches'
import type { Category, Product } from '../types'

const LOW_STOCK = 5

function stockLabel(quantity: number) {
  if (quantity === 0) return 'Sold out'
  if (quantity <= LOW_STOCK) return `Only ${quantity} left`
  return `${quantity} in stock`
}

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [related, setRelated] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [size, setSize] = useState<string | null>(null)
  const [zoom, setZoom] = useState<{ x: number; y: number } | null>(null)
  const { ask } = useChatUI()

  useEffect(() => {
    setProduct(null)
    setError(null)
    setSize(null)
    window.scrollTo({ top: 0 })
    fetchProduct(productId)
      .then(setProduct)
      .catch((e: Error) => setError(e.message))
  }, [productId])

  // "More in this category": same aisle, in-stock first, from the shared (cached) catalogue.
  useEffect(() => {
    if (!product) return
    fetchCategories().then(setCategories).catch(() => {})
    fetchProducts()
      .then((all) =>
        setRelated(
          all
            .filter((p) => p.category === product.category && p.product_id !== product.product_id)
            .sort((a, b) => (b.total_stock ?? 0) - (a.total_stock ?? 0))
            .slice(0, 4),
        ),
      )
      .catch(() => setRelated([]))
  }, [product])

  if (error) {
    return (
      <div className="page narrow">
        <h1>Product not found</h1>
        <p className="muted">We couldn't find that item ({error}).</p>
        <Link to="/products" className="btn btn-pink">
          Back to products
        </Link>
      </div>
    )
  }
  if (!product) return <div className="page muted">Loading…</div>

  const inventory = product.inventory ?? []
  const totalStock = inventory.reduce((sum, s) => sum + s.quantity, 0)
  const category = categories.find((c) => c.slug === product.category)
  const picked = inventory.find((s) => s.size === size)

  // Zoom lens: the photo magnifies 2.2x and follows the cursor.
  function onZoom(e: MouseEvent<HTMLDivElement>) {
    const r = e.currentTarget.getBoundingClientRect()
    setZoom({ x: ((e.clientX - r.left) / r.width) * 100, y: ((e.clientY - r.top) / r.height) * 100 })
  }

  return (
    <div className="page">
      <nav className="crumbs" aria-label="Breadcrumb">
        <Link to="/">Home</Link>
        <span>/</span>
        <Link to="/products">Shop</Link>
        {category && (
          <>
            <span>/</span>
            <Link to={`/products?category=${category.slug}`}>{category.label}</Link>
          </>
        )}
        <span>/</span>
        <span aria-current="page">{product.name}</span>
      </nav>
      <div className="detail">
        <div
          className={`detail-img ${zoom ? 'zooming' : ''}`}
          onMouseMove={onZoom}
          onMouseLeave={() => setZoom(null)}
          style={zoom ? { backgroundImage: `url(${product.image_url})`, backgroundPosition: `${zoom.x}% ${zoom.y}%` } : undefined}
        >
          <img src={product.image_url} alt={product.name} />
          <span className="zoom-hint">{zoom ? 'Move to explore' : 'Hover to zoom'}</span>
        </div>
        <div className="detail-info">
          <span className="eyebrow">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <div className="detail-price">{formatPrice(product.price)}</div>
          <p className="detail-desc">{product.description}</p>

          <h3>Colors</h3>
          <div className="detail-swatches">
            {uniqueSwatches(product.colors).map((s) => (
              <span key={s.name} className="detail-swatch">
                <span className="swatch swatch-lg" style={{ background: s.fill }} />
                {s.name}
              </span>
            ))}
          </div>

          <h3>
            Choose a size <span className="muted small">({totalStock} in stock across sizes)</span>
          </h3>
          <div className="sizes" role="radiogroup" aria-label="Size">
            {inventory.map((s) => (
              <button
                key={s.size}
                role="radio"
                aria-checked={size === s.size}
                className={`size ${s.quantity === 0 ? 'size-out' : s.quantity <= LOW_STOCK ? 'size-low' : ''} ${size === s.size ? 'size-picked' : ''}`}
                onClick={() => setSize(s.size)}
              >
                <span className="size-name">{s.size}</span>
                <span className="size-qty">{stockLabel(s.quantity)}</span>
              </button>
            ))}
          </div>
          {picked && (
            <p className={`size-verdict ${picked.quantity === 0 ? 'out' : ''}`} aria-live="polite">
              {picked.quantity === 0
                ? `${picked.size} is sold out right now.`
                : picked.quantity <= LOW_STOCK
                  ? `Good news: ${picked.size} is in stock, but only ${picked.quantity} left.`
                  : `${picked.size} is in stock (${picked.quantity} available).`}
            </p>
          )}

          <div className="concierge-card">
            <div className="concierge-card-head">
              <Crest size={22} />
              <span>
                <strong>Ask the Concierge</strong>
                <span className="muted small">Answers come straight from our live stockroom.</span>
              </span>
            </div>
            <div className="concierge-asks">
              {[
                picked
                  ? picked.quantity === 0
                    ? `${picked.size} is sold out. What’s similar in ${picked.size}?`
                    : `How many ${picked.size} are left?`
                  : 'Is this in stock in a medium?',
                'Do you have this in another color?',
                `What else goes with the ${product.name}?`,
              ].map((q) => (
                <button key={q} className="suggest-chip" onClick={() => ask(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>

          <h3>Tags</h3>
          <div className="chips">
            {product.search_tags.map((t) => (
              <span key={t} className="chip chip-dim">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      {related.length > 0 && (
        <section className="section related">
          <div className="section-head">
            <div>
              <span className="eyebrow">You may also like</span>
              <h2>More {category?.label ?? 'like this'}</h2>
            </div>
            {category && (
              <Link to={`/products?category=${category.slug}`} className="link-pink">
                All {category.count} {category.label.toLowerCase()} →
              </Link>
            )}
          </div>
          <div className="grid">
            {related.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
