import { useRef } from 'react'
import type { CSSProperties, MouseEvent } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import { uniqueSwatches } from '../swatches'
import type { Product } from '../types'

type CardProduct = Pick<Product, 'product_id' | 'name' | 'price' | 'garment_type' | 'description' | 'image_url'> &
  Partial<Pick<Product, 'colors' | 'stock'>>

interface Props {
  product: CardProduct
  className?: string
  style?: CSSProperties
}

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
const LOW_STOCK = 5

const shorten = (text: string, max = 96) =>
  text.length <= max ? text : `${text.slice(0, text.lastIndexOf(' ', max))}…`

/** Honest urgency from live stock: the scarcest in-stock size, if 5 or fewer are left. */
function stockBadge(stock?: Record<string, number>) {
  if (!stock) return null
  const sizes = SIZES.filter((s) => s in stock)
  if (sizes.length && sizes.every((s) => stock[s] === 0)) return { text: 'Sold out', tone: 'out' }
  const low = sizes.filter((s) => stock[s] > 0 && stock[s] <= LOW_STOCK).sort((a, b) => stock[a] - stock[b])[0]
  return low ? { text: `Only ${stock[low]} left in ${low}`, tone: 'low' } : null
}

/**
 * Used by the catalogue grid, Home, "More …" rows, and the chat's page results; every card opens /products/:id.
 * Problem 10: color swatches, size availability strip, low-stock badge, and a 3D tilt with a light glare.
 */
export default function ProductCard({ product, className, style }: Props) {
  const ref = useRef<HTMLAnchorElement>(null)
  const swatches = uniqueSwatches(product.colors ?? []).slice(0, 5)
  const badge = stockBadge(product.stock)

  function onMove(e: MouseEvent<HTMLAnchorElement>) {
    const el = ref.current
    if (!el || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const r = el.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width
    const y = (e.clientY - r.top) / r.height
    el.style.setProperty('--rx', `${(0.5 - y) * 7}deg`)
    el.style.setProperty('--ry', `${(x - 0.5) * 9}deg`)
    el.style.setProperty('--gx', `${x * 100}%`)
    el.style.setProperty('--gy', `${y * 100}%`)
  }
  function onLeave() {
    const el = ref.current
    if (!el) return
    el.style.setProperty('--rx', '0deg')
    el.style.setProperty('--ry', '0deg')
  }

  return (
    <Link
      ref={ref}
      to={`/products/${product.product_id}`}
      className={`card card-tilt ${className ?? ''}`}
      style={style}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
    >
      <div className="card-img">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {badge && <span className={`card-badge badge-${badge.tone}`}>{badge.text}</span>}
        <span className="card-glare" aria-hidden />
      </div>
      <div className="card-body">
        <div className="card-top">
          <h3 className="card-title">{product.name}</h3>
          <span className="price">{formatPrice(product.price)}</span>
        </div>
        <p className="card-type">{product.garment_type}</p>
        <p className="card-desc">{shorten(product.description)}</p>
        {(swatches.length > 0 || product.stock) && (
          <div className="card-meta">
            {swatches.length > 0 && (
              <span className="swatches" aria-label={`Colors: ${(product.colors ?? []).join(', ')}`}>
                {swatches.map((s) => (
                  <span key={s.name} className="swatch" title={s.name} style={{ background: s.fill }} />
                ))}
              </span>
            )}
            {product.stock && (
              <span className="size-strip" aria-label="Sizes in stock">
                {SIZES.filter((s) => s in product.stock!).map((s) => (
                  <span key={s} className={product.stock![s] > 0 ? 'in' : 'out'} title={`${s}: ${product.stock![s]} left`}>
                    {s}
                  </span>
                ))}
              </span>
            )}
          </div>
        )}
      </div>
    </Link>
  )
}
