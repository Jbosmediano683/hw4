import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Scroll-reveal (Problem 10): elements with class "reveal" fade and rise into place the first time
 * they scroll into view. Re-scans on every route change and whenever new .reveal nodes appear.
 * Skipped entirely for shoppers who prefer reduced motion (CSS shows them immediately).
 */
export function useReveal() {
  const location = useLocation()

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-visible'))
      return
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            e.target.classList.add('is-visible')
            io.unobserve(e.target)
          }
        }
      },
      { rootMargin: '0px 0px -8% 0px', threshold: 0.08 },
    )
    const scan = () =>
      document.querySelectorAll('.reveal:not(.is-visible)').forEach((el) => io.observe(el))
    scan()
    const mo = new MutationObserver(scan)
    mo.observe(document.body, { childList: true, subtree: true })
    return () => {
      io.disconnect()
      mo.disconnect()
    }
  }, [location.pathname])
}
