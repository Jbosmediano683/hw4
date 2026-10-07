import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { fetchCategories } from '../api'
import { useAuth } from '../auth'
import type { Category } from '../types'
import Crest from './Crest'

export default function NavBar() {
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [categories, setCategories] = useState<Category[]>([])
  const [shopOpen, setShopOpen] = useState(false)
  const shopRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  // Close the Shop menu on navigation or an outside click.
  useEffect(() => setShopOpen(false), [location.pathname, location.search])
  useEffect(() => {
    if (!shopOpen) return
    const onClick = (e: MouseEvent) => {
      if (!shopRef.current?.contains(e.target as Node)) setShopOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setShopOpen(false)
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [shopOpen])

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  const total = categories.reduce((n, c) => n + c.count, 0)

  return (
    <header className="nav">
      <div className="ribbon">
        <span>Fall semester on campus</span>
        <span className="ribbon-dot">✦</span>
        <span>Long-sleeve season is here</span>
        <span className="ribbon-dot">✦</span>
        <span>New Haven, Connecticut</span>
      </div>
      <div className="nav-inner">
        <Link to="/" className="brand" aria-label="Campus Customs home">
          <Crest />
          <span className="brand-text">
            <span className="brand-name">Campus Customs</span>
            <span className="brand-sub">New Haven · Connecticut</span>
          </span>
        </Link>

        <nav className="nav-links" aria-label="Main">
          <NavLink to="/" end className="nav-link">
            Home
          </NavLink>
          <div className="shop-menu" ref={shopRef} onMouseLeave={() => setShopOpen(false)}>
            <button
              className={`nav-link nav-link-btn ${location.search.includes('category=') ? 'active' : ''}`}
              aria-haspopup="true"
              aria-expanded={shopOpen}
              onClick={() => setShopOpen((o) => !o)}
              onMouseEnter={() => setShopOpen(true)}
            >
              Shop <span className="caret">▾</span>
            </button>
            {shopOpen && (
              <div className="mega" role="menu">
                <div className="mega-head">
                  <span className="eyebrow">Shop by apparel</span>
                  <Link to="/products" className="link-pink small">
                    View all {total || ''} →
                  </Link>
                </div>
                <div className="mega-grid">
                  {categories.map((c) => (
                    <Link key={c.slug} to={`/products?category=${c.slug}`} className="mega-item" role="menuitem">
                      <img src={c.image_url} alt="" />
                      <span>
                        <span className="mega-label">{c.label}</span>
                        <span className="mega-count">{c.count} styles</span>
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
          <NavLink to="/products" end className="nav-link">
            Products
          </NavLink>
          <NavLink to="/about" className="nav-link">
            About Us
          </NavLink>
        </nav>

        <div className="nav-auth">
          {loading ? null : user ? (
            <>
              <span className="nav-user">
                <span className="avatar">{(user.first_name ?? user.name).charAt(0).toUpperCase()}</span>
                Hi, {user.first_name ?? user.name}
              </span>
              <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="nav-link">
                Log In
              </NavLink>
              <NavLink to="/signup" className="btn btn-pink btn-sm">
                Create account
              </NavLink>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
