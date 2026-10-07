import { Link } from 'react-router-dom'
import StoreGallery from '../components/StoreGallery'

export default function About() {
  return (
    <div className="page about">
      <div className="about-copy">
        <span className="eyebrow">About Us</span>
        <h1>Made in New Haven, worn everywhere</h1>
        <p className="lead">
          Campus Customs began with one simple idea: Yale spirit shouldn't only come out on game day. We design gear
          you'll actually want to wear on a Tuesday, whether that's to a morning seminar, a late night in the library,
          or a trip home for the holidays.
        </p>

        <blockquote className="about-quote">
          Remember the first cold morning of the fall semester, pulling on a sweatshirt and walking to class under the
          elms? That's the feeling we fold into every piece.
        </blockquote>

        <h2>What we stand for</h2>
        <ul className="about-list">
          <li>
            <strong>Tradition with a modern fit.</strong> We take the classic Yale marks and Bulldog style and put
            them on cuts and fabrics that feel current.
          </li>
          <li>
            <strong>Something for the whole community.</strong> Undergrads, grad students, alumni, faculty, and the
            parents and grandparents who brag about them can all find a piece here.
          </li>
          <li>
            <strong>Local roots.</strong> We're a family-run shop at 57 Broadway, right across from campus, and we've
            been selling Yale gear on Broadway since the 1970s. We still know many of our customers by name.
          </li>
        </ul>

        <h2>What you'll find</h2>
        <p>
          Hoodies, crewnecks, quarter-zips, tees, and jackets, including pieces for every residential college,
          designs for Yale's varsity teams, and limited runs for rivalry weekend. Every product page shows live stock
          by size, so you'll know what's available before you ask.
        </p>

        <h2>Come say hello</h2>
        <p>
          Stop by the shop at <strong>57 Broadway, New Haven</strong> next time you're back for a reunion or The Game.
          Or tap <strong>Ask the Concierge</strong> in the corner, or{' '}
          <Link to="/products" className="link-pink">
            browse the full collection
          </Link>
          .
        </p>
      </div>

      <aside className="about-photos" aria-label="Photos of the Campus Customs shop">
        <StoreGallery />
      </aside>
    </div>
  )
}
