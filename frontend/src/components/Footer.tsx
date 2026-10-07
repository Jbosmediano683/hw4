import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCategories } from '../api'
import type { Category } from '../types'
import Crest from './Crest'

export default function Footer() {
  const [categories, setCategories] = useState<Category[]>([])
  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <Crest size={44} />
          <div>
            <div className="footer-name">Campus Customs</div>
            <p className="muted">Bulldog apparel for the whole Yale family. New Haven, Connecticut.</p>
          </div>
        </div>
        <div className="footer-col">
          <h4>Shop</h4>
          {categories.map((c) => (
            <Link key={c.slug} to={`/products?category=${c.slug}`}>
              {c.label}
            </Link>
          ))}
        </div>
        <div className="footer-col">
          <h4>Campus Customs</h4>
          <Link to="/about">About Us</Link>
          <Link to="/products">All products</Link>
          <Link to="/login">Log In</Link>
          <Link to="/signup">Create account</Link>
        </div>
      </div>
      <div className="footer-base">
        <span>✦ Made for Bulldogs, worn every fall ✦</span>
      </div>
    </footer>
  )
}
