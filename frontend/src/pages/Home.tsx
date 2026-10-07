import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCategories, fetchProducts } from '../api'
import { useChatUI } from '../chatUI'
import ProductCard from '../components/ProductCard'
import type { Category, Product } from '../types'

const FEATURED_IDS = [
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'brooks-brothers-bomber-jacket-yale',
  'boola-boola-t-shirt',
]

// The headline's rotating audience.
const AUDIENCES = ['crisp fall days.', 'students.', 'alumni.', 'parents.', 'game day.', 'sweater weather.']

// Yale's fourteen residential colleges: each name in the marquee asks the concierge.
// `crest` = shield cut from that college's own Campus Customs product photo (public/crests/, made by
// scripts/extract_crests.py). Colleges we don't carry yet get a plain Yale-blue shield, not invented arms.
const COLLEGES: { name: string; crest?: string }[] = [
  { name: 'Benjamin Franklin', crest: 'benjamin-franklin' },
  { name: 'Berkeley', crest: 'berkeley' },
  { name: 'Branford', crest: 'branford' },
  { name: 'Davenport', crest: 'davenport' },
  { name: 'Ezra Stiles' },
  { name: 'Grace Hopper', crest: 'grace-hopper' },
  { name: 'Jonathan Edwards', crest: 'jonathan-edwards' },
  { name: 'Morse', crest: 'morse' },
  { name: 'Pauli Murray' },
  { name: 'Pierson', crest: 'pierson' },
  { name: 'Saybrook', crest: 'saybrook' },
  { name: 'Silliman' },
  { name: 'Timothy Dwight', crest: 'timothy-dwight' },
  { name: 'Trumbull', crest: 'trumbull' },
]

/** A college crest from public/crests/; falls back to the plain shield if the file isn't there
 *  (crests are generated locally from the data pack and are not committed to the repo). */
function CrestImage({ slug }: { slug: string }) {
  const [failed, setFailed] = useState(false)
  return failed ? <PlainShield /> : <img src={`/crests/${slug}.png`} alt="" loading="lazy" onError={() => setFailed(true)} />
}

/** Stand-in for colleges without a product photo: a plain Yale-blue shield (no invented arms). */
function PlainShield() {
  return (
    <svg viewBox="0 0 40 46" className="monogram-shield">
      <path d="M2 1.5h36v23.5c0 9.6-7.6 16.7-18 20C9.6 41.7 2 34.6 2 25Z" fill="#00356B" stroke="#ffffff" strokeOpacity="0.7" strokeWidth="1.4" />
      <path d="M20 13l2.2 6.6h6.8l-5.5 4 2.1 6.6-5.6-4.1-5.6 4.1 2.1-6.6-5.5-4h6.8Z" fill="#ffffff" fillOpacity="0.85" />
    </svg>
  )
}

// Curated edits: editorial collages whose button hands a real question to the concierge.
const EDITS = [
  {
    kicker: 'The Game Edit',
    title: 'Harvard–Yale, dressed for the Bowl',
    ids: ['2025-yale-vs-harvard-t-shirt', 'ua-gameday-double-knit-hood', 'boola-boola-t-shirt'],
    ask: 'What should I wear to The Game against Harvard?',
  },
  {
    kicker: 'Sweater Weather',
    title: 'Quarter-zips & fleece for crisp New Haven mornings',
    ids: ['branford-1-4-zip', 'benjamin-franklin-fleece-jacket', 'trumbull-1-4-zip'],
    ask: 'What quarter-zips and fleece do you have for fall?',
  },
  {
    kicker: 'The Family Collection',
    title: 'For the proudest Yale mom, dad & grandparents',
    ids: ['yale-mom-hoodie', 'yale-dad-hoodie', 'yale-grandpa-hoodie'],
    ask: 'Show me the Yale family hoodies for mom, dad, and grandparents',
  },
]

const pillars = [
  {
    no: '01',
    title: 'Made for every Bulldog',
    text: 'Students, grads, parents, and the friends who cheer from the stands. There is a fit for everyone in the family.',
  },
  {
    no: '02',
    title: 'Your college, your team',
    text: 'Show off your residential college or the sport you never miss, from Branford to Berkeley and from the rink to the pool.',
  },
  {
    no: '03',
    title: 'A concierge, not a search box',
    text: 'Ask for a size, a color, or a college and our assistant checks the live stockroom, then lays the options out for you.',
  },
]

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [word, setWord] = useState(0)
  const { ask } = useChatUI()

  useEffect(() => {
    fetchProducts().then(setProducts).catch(() => setProducts([]))
    fetchCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const t = setInterval(() => setWord((w) => (w + 1) % AUDIENCES.length), 2400)
    return () => clearInterval(t)
  }, [])

  const byId = new Map(products.map((p) => [p.product_id, p]))
  const featured = FEATURED_IDS.map((id) => byId.get(id)).filter((p): p is Product => !!p)

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">The Fall Semester Collection · New Haven</span>
          <h1>
            Classic Yale style, made for{' '}
            <span className="word-roll" aria-live="polite">
              <em key={word} className="pink">
                {AUDIENCES[word]}
              </em>
            </span>
          </h1>
          <p className="lead">
            When the elms on Old Campus turn gold and long sleeves become the norm, Campus Customs has you covered:
            heavyweight hoodies, crisp crewnecks, quarter-zips for the seminar room, and fleece for the walk home.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-pink">
              Shop the collection
            </Link>
            <button className="btn btn-ghost" onClick={() => ask('What hoodies do you have?')}>
              <span className="spark">✦</span> Ask the Concierge
            </button>
          </div>
        </div>
        <div className="hero-art" aria-hidden>
          {featured.slice(0, 3).map((p) => (
            <img key={p.product_id} src={p.image_url} alt="" />
          ))}
        </div>
      </section>

      <section className="marquee" aria-label="Shop by residential college">
        <span className="marquee-label">Shop your college</span>
        <div className="marquee-window">
          <div className="marquee-track">
            {[...COLLEGES, ...COLLEGES].map((c, i) => (
              <button
                key={i}
                className="marquee-item"
                onClick={() => ask(`Do you have anything for ${c.name} College?`)}
                tabIndex={i < COLLEGES.length ? 0 : -1}
                aria-hidden={i >= COLLEGES.length}
                title={`Ask the concierge about ${c.name} College`}
              >
                <span className="marquee-seal">
                  <span className="marquee-crest" aria-hidden>
                    {c.crest ? <CrestImage slug={c.crest} /> : <PlainShield />}
                  </span>
                  <span className="marquee-name">{c.name}</span>
                </span>
                <span className="marquee-dot">✦</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="section reveal">
        <div className="ornament" aria-hidden>
          <span>✦</span>
        </div>
        <div className="section-head centered">
          <div>
            <span className="eyebrow">No. 01 · Shop by apparel</span>
            <h2>Find your fit</h2>
          </div>
        </div>
        <div className="cat-tiles">
          {categories.map((c) => (
            <Link key={c.slug} to={`/products?category=${c.slug}`} className="cat-tile">
              <div className="cat-tile-img">
                <img src={c.image_url} alt="" loading="lazy" />
              </div>
              <div className="cat-tile-body">
                <span className="cat-tile-label">{c.label}</span>
                <span className="cat-tile-count">{c.count} styles →</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="section reveal">
        <div className="section-head">
          <div>
            <span className="eyebrow">No. 02 · Curated edits</span>
            <h2>
              Picked by the <em>concierge</em>
            </h2>
          </div>
        </div>
        <div className="edits">
          {EDITS.map((e) => (
            <article key={e.kicker} className="edit">
              <div className="edit-collage">
                {e.ids.map((id) => {
                  const p = byId.get(id)
                  return p ? <img key={id} src={p.image_url} alt={p.name} loading="lazy" /> : null
                })}
              </div>
              <div className="edit-body">
                <span className="edit-kicker">{e.kicker}</span>
                <h3>{e.title}</h3>
                <button className="edit-ask" onClick={() => ask(e.ask)}>
                  <span className="spark">✦</span> Ask the Concierge to pull these →
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="pillars reveal">
        {pillars.map((p) => (
          <div key={p.title} className="pillar">
            <span className="pillar-no">{p.no}</span>
            <h3>{p.title}</h3>
            <p className="muted">{p.text}</p>
          </div>
        ))}
      </section>

      <section className="section reveal">
        <div className="section-head">
          <div>
            <span className="eyebrow">No. 03 · Fan favorites</span>
            <h2>The essentials</h2>
          </div>
          <Link to="/products" className="link-pink">
            View all →
          </Link>
        </div>
        <div className="grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>
    </>
  )
}
