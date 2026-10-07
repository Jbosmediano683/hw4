import { useState } from 'react'
import type { ReactNode } from 'react'

/**
 * About page photo wall: polaroids of the shop at 57 Broadway.
 *
 * Drop real photos into frontend/public/about/ with the file names below and they appear
 * automatically. Until a photo exists, its frame shows an original illustration, labeled as such,
 * so nothing on the page pretends to be a photo of the real store.
 */
const PHOTOS: { src: string; caption: string; alt: string; art: () => ReactNode }[] = [
  {
    src: '/about/storefront.jpg',
    caption: '57 Broadway, New Haven',
    alt: 'The Campus Customs storefront on Broadway in New Haven',
    art: StorefrontArt,
  },
  {
    src: '/about/interior-1.jpg',
    caption: 'The sweatshirt wall',
    alt: 'Inside Campus Customs: shelves of folded Yale sweatshirts',
    art: ShelvesArt,
  },
  {
    src: '/about/interior-2.jpg',
    caption: 'Pennants by the register',
    alt: 'Inside Campus Customs: Yale pennants above the counter',
    art: CounterArt,
  },
]

function Polaroid({ photo, index }: { photo: (typeof PHOTOS)[number]; index: number }) {
  const [failed, setFailed] = useState(false)
  const Art = photo.art
  return (
    <figure className={`polaroid polaroid-${index}`}>
      <span className="tape" aria-hidden />
      <div className="polaroid-img">
        {failed ? (
          <div className="polaroid-art" role="img" aria-label={`Illustration: ${photo.alt}`}>
            <Art />
          </div>
        ) : (
          <img src={photo.src} alt={photo.alt} onError={() => setFailed(true)} />
        )}
      </div>
      <figcaption>
        {photo.caption}
        {failed && <span className="polaroid-note">illustration</span>}
      </figcaption>
    </figure>
  )
}

export default function StoreGallery() {
  return (
    <div className="store-gallery">
      {PHOTOS.map((p, i) => (
        <Polaroid key={p.src} photo={p} index={i} />
      ))}
    </div>
  )
}

/* ---------- placeholder illustrations (shown only until real photos are added) ---------- */

function StorefrontArt() {
  return (
    <svg viewBox="0 0 320 240" preserveAspectRatio="xMidYMid slice">
      <defs>
        <pattern id="brick" width="24" height="12" patternUnits="userSpaceOnUse">
          <rect width="24" height="12" fill="#8a3f2c" />
          <path d="M0 0h24M0 6h24M0 12h24M12 0v6M0 6v6M24 6v6" stroke="#6e2f20" strokeWidth="1" />
        </pattern>
        <linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#ffe2a8" />
          <stop offset="1" stopColor="#f2b56b" />
        </linearGradient>
      </defs>
      <rect width="320" height="240" fill="#2b3f6e" />
      <rect y="18" width="320" height="200" fill="url(#brick)" />
      {/* sign */}
      <rect x="40" y="30" width="240" height="34" rx="3" fill="#00356B" stroke="#d9c79a" strokeWidth="2" />
      <text x="160" y="53" textAnchor="middle" fontFamily="'Cormorant Garamond', Georgia, serif" fontSize="20" fontWeight="700" fill="#fff" letterSpacing="2">
        CAMPUS CUSTOMS
      </text>
      {/* striped awning */}
      {Array.from({ length: 12 }, (_, i) => (
        <path key={i} d={`M${30 + i * 21.7} 72h21.7l-4 22h-21.7z`} fill={i % 2 ? '#ffffff' : '#00356B'} />
      ))}
      <path d="M26 94h270" stroke="#0b2648" strokeWidth="3" />
      {/* windows with warm light and hoodies on display */}
      {[48, 196].map((x) => (
        <g key={x}>
          <rect x={x} y="104" width="78" height="88" fill="url(#glow)" stroke="#3a2418" strokeWidth="4" />
          <path d={`M${x + 14} 186v-34l12-10h14l12 10v34z`} fill="#1c2a4a" />
          <path d={`M${x + 50} 186v-28l9-8h10l9 8v28z`} fill="#a9a9ad" opacity="0.9" />
          <text x={x + 39} y="170" textAnchor="middle" fontFamily="Georgia, serif" fontSize="9" fontWeight="700" fill="#fff">
            YALE
          </text>
        </g>
      ))}
      {/* door */}
      <rect x="138" y="104" width="44" height="114" fill="#0b2648" stroke="#3a2418" strokeWidth="4" />
      <rect x="146" y="112" width="28" height="44" fill="url(#glow)" opacity="0.85" />
      <circle cx="174" cy="166" r="2.5" fill="#d9c79a" />
      <text x="160" y="100" textAnchor="middle" fontFamily="Georgia, serif" fontSize="9" fill="#fff">
        57
      </text>
      {/* sidewalk, mums, leaves */}
      <rect y="218" width="320" height="22" fill="#4a4a50" />
      {[22, 292].map((x) => (
        <g key={x}>
          <rect x={x - 10} y="204" width="20" height="16" fill="#5a3a26" />
          <circle cx={x - 6} cy="200" r="7" fill="#e0823a" />
          <circle cx={x + 5} cy="198" r="8" fill="#d9a441" />
          <circle cx={x} cy="193" r="6" fill="#c8553d" />
        </g>
      ))}
      {[[70, 228], [110, 232], [210, 226], [250, 233]].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="3" fill={['#e0823a', '#c8553d', '#d9a441', '#e0823a'][i]} />
      ))}
    </svg>
  )
}

function ShelvesArt() {
  const colors = ['#1c2a4a', '#a9a9ad', '#f4efe2', '#1c2a4a', '#5d5e63', '#2f5aa8']
  return (
    <svg viewBox="0 0 240 200" preserveAspectRatio="xMidYMid slice">
      <rect width="240" height="200" fill="#e9dcc3" />
      <rect y="150" width="240" height="50" fill="#8a6440" />
      {[30, 80, 130].map((y) => (
        <g key={y}>
          <rect x="10" y={y + 22} width="220" height="6" fill="#6b4a2c" />
          {Array.from({ length: 6 }, (_, i) => (
            <g key={i}>
              {[0, 1, 2].map((k) => (
                <rect key={k} x={18 + i * 36} y={y + 16 - k * 7} width="30" height="6" rx="1.5" fill={colors[(i + k + y / 10) % colors.length]} />
              ))}
            </g>
          ))}
        </g>
      ))}
      <circle cx="60" cy="8" r="7" fill="#ffd27a" />
      <circle cx="180" cy="8" r="7" fill="#ffd27a" />
    </svg>
  )
}

function CounterArt() {
  return (
    <svg viewBox="0 0 240 200" preserveAspectRatio="xMidYMid slice">
      <rect width="240" height="200" fill="#efe3c8" />
      {[[30, 'YALE'], [100, 'BULLDOGS'], [170, 'BOOLA']].map(([x, label]) => (
        <g key={label as string} transform={`rotate(-6 ${(x as number) + 30} 40)`}>
          <path d={`M${x} 24h66l-66 30z`} fill="#00356B" />
          <text x={(x as number) + 8} y="37" fontFamily="Georgia, serif" fontSize="8" fontWeight="700" fill="#fff">
            {label}
          </text>
        </g>
      ))}
      <rect x="20" y="120" width="200" height="60" fill="#6b4a2c" />
      <rect x="20" y="114" width="200" height="8" fill="#8a6440" />
      <rect x="150" y="92" width="40" height="22" rx="3" fill="#2a2a30" />
      <rect x="156" y="96" width="28" height="9" fill="#9bd28f" opacity="0.8" />
      <path d="M40 114v-26h40v26" fill="#a9a9ad" />
      <path d="M48 96h24" stroke="#1c2a4a" strokeWidth="3" />
      <rect y="180" width="240" height="20" fill="#5a3a26" />
    </svg>
  )
}
