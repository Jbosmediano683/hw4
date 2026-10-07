/**
 * Fall on campus (Problem 10 revision): a fixed backdrop behind every page.
 * Dusk sky in Yale blue fading to a warm October glow, a Gothic skyline with a Harkness-style
 * tower and lit leaded windows, autumn elms in maple red / pumpkin / gold, and leaves drifting
 * down the page. Pure SVG + CSS (no image downloads); leaves stop under prefers-reduced-motion.
 */

const LEAF = 'M12 1.5 13.7 6.6 18.3 5 16.7 9.6 21.6 10.8 17.4 13.6 19 17.6 13.8 16 12.7 22h-1.4L10.2 16 5 17.6 6.6 13.6 2.4 10.8 7.3 9.6 5.7 5 10.3 6.6Z'
const LEAF_COLORS = ['#e2563a', '#f08a2c', '#f2b636', '#c2412b', '#f5c451', '#d8692a']

// Deterministic "random" so the scene is the same on every render.
const leaves = Array.from({ length: 22 }, (_, i) => {
  const r = (n: number) => ((Math.sin(i * 12.9898 + n * 78.233) * 43758.5453) % 1 + 1) % 1
  return {
    left: `${Math.round(r(1) * 100)}%`,
    size: 16 + Math.round(r(2) * 18),
    duration: `${16 + Math.round(r(3) * 14)}s`,
    delay: `-${Math.round(r(4) * 30)}s`,
    sway: `${3 + Math.round(r(5) * 4)}s`,
    color: LEAF_COLORS[i % LEAF_COLORS.length],
    opacity: 0.55 + r(6) * 0.4,
  }
})

// Rounded autumn canopy: a cluster of overlapping circles.
function Elm({ x, y, s, colors }: { x: number; y: number; s: number; colors: string[] }) {
  const blobs = [
    [0, 0, 1], [-0.7, 0.25, 0.75], [0.7, 0.2, 0.8], [-0.35, -0.5, 0.7], [0.4, -0.45, 0.72], [0, 0.55, 0.7],
  ]
  return (
    <g>
      <rect x={x - s * 0.08} y={y + s * 0.5} width={s * 0.16} height={s * 1.6} fill="#1a1410" />
      {blobs.map(([dx, dy, k], i) => (
        <circle key={i} cx={x + dx * s} cy={y + dy * s} r={k * s * 0.62} fill={colors[i % colors.length]} />
      ))}
    </g>
  )
}

export default function CampusBackdrop() {
  return (
    <div className="backdrop" aria-hidden>
      <div className="backdrop-sky" />
      <div className="backdrop-glow" />

      <svg className="backdrop-skyline" viewBox="0 0 1440 420" preserveAspectRatio="xMidYMax slice">
        {/* far hills and trees, softened by haze */}
        <path d="M0 330 Q180 290 360 318 T720 312 T1080 300 T1440 316 V420 H0Z" fill="#3b2a3d" opacity="0.55" />
        {[60, 210, 470, 640, 900, 1160, 1330].map((x, i) => (
          <Elm key={x} x={x} y={300} s={34 + (i % 3) * 6} colors={['#9a4630', '#a8602c', '#8a6a30']} />
        ))}

        {/* Gothic campus silhouette */}
        <g fill="#06142b">
          {/* left college wall with crenellations */}
          <path d="M120 420V300h20v-12h16v12h20v-12h16v12h20v-12h16v12h20v-12h16v12h20v120Z" />
          <path d="M300 420V270l30-34 30 34v150Z" />
          {/* Harkness-style tower */}
          <path d="M610 420V250h18V170h10v-18h8v-30h8l6-40 6 40h8v30h8v18h10v80h18v170Z" />
          <path d="M600 250h80v12h-80z" />
          {/* pinnacles */}
          <path d="M628 170l4-22 4 22zM672 170l-4-22-4 22zM646 122l2-14 2 14zM658 122l-2-14-2 14z" />
          {/* library nave with pointed arches */}
          <path d="M760 420V300l40-46 40 46v-18h120v138Z" />
          <path d="M960 420V292h26v-14h14v14h26v-14h14v14h26v128Z" />
          {/* right chapel spire */}
          <path d="M1150 420V286h24l18-90 18 90h24v134Z" />
          <path d="M1270 420V310h120v110Z" />
        </g>

        {/* warm lit windows */}
        <g fill="#ffd27a">
          {[[140, 330], [180, 330], [220, 330], [260, 330], [315, 300], [345, 300], [628, 280], [664, 280], [646, 210],
            [790, 330], [820, 330], [880, 320], [920, 320], [990, 320], [1030, 320], [1070, 320], [1185, 320], [1290, 340], [1330, 340], [1370, 340]].map(
            ([x, y], i) => (
              <path key={i} d={`M${x} ${y + 16}v-10a4 5 0 0 1 8 0v10z`} className={i % 4 === 0 ? 'window-flicker' : undefined} />
            ),
          )}
        </g>

        {/* lamp posts with glow */}
        {[440, 1100].map((x) => (
          <g key={x}>
            <circle cx={x} cy={344} r={26} fill="url(#lamp)" />
            <rect x={x - 1.5} y={346} width={3} height={60} fill="#06142b" />
            <circle cx={x} cy={344} r={4} fill="#ffe3a3" />
          </g>
        ))}

        {/* foreground elms in full color */}
        <Elm x={30} y={350} s={70} colors={['#e2563a', '#f08a2c', '#c2412b']} />
        <Elm x={230} y={368} s={48} colors={['#f2b636', '#f08a2c', '#f5c451']} />
        <Elm x={520} y={360} s={58} colors={['#f2b636', '#f5c451', '#f08a2c']} />
        <Elm x={735} y={372} s={42} colors={['#e2563a', '#d8692a', '#f08a2c']} />
        <Elm x={1040} y={368} s={46} colors={['#f5c451', '#f2b636', '#e2563a']} />
        <Elm x={1240} y={355} s={66} colors={['#f08a2c', '#e2563a', '#f2b636']} />
        <Elm x={1420} y={350} s={74} colors={['#c2412b', '#e2563a', '#d8692a']} />

        {/* leaf-strewn lawn */}
        <path d="M0 400 Q360 388 720 396 T1440 392 V420 H0Z" fill="#14231a" />
        <defs>
          <radialGradient id="lamp">
            <stop offset="0" stopColor="#ffd27a" stopOpacity="0.55" />
            <stop offset="1" stopColor="#ffd27a" stopOpacity="0" />
          </radialGradient>
        </defs>
      </svg>

      <div className="leaves">
        {leaves.map((l, i) => (
          <span
            key={i}
            className="leaf"
            style={{ left: l.left, animationDuration: l.duration, animationDelay: l.delay, opacity: l.opacity }}
          >
            <svg
              width={l.size}
              height={l.size}
              viewBox="0 0 24 24"
              style={{ animationDuration: l.sway, color: l.color }}
              className="leaf-sway"
            >
              <path d={LEAF} fill="currentColor" />
              <path d="M12 22V9" stroke="rgba(0,0,0,0.25)" strokeWidth="0.8" />
            </svg>
          </span>
        ))}
      </div>
    </div>
  )
}
