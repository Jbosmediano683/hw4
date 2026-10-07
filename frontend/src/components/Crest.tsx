/** Campus Customs shield monogram: a heraldic crest drawn in SVG (no image request). */
export default function Crest({ size = 36 }: { size?: number }) {
  return (
    <svg
      className="crest"
      width={size}
      height={size * 1.15}
      viewBox="0 0 40 46"
      aria-hidden
      focusable="false"
    >
      <path
        d="M20 1.5 37 6.5v15.2c0 10.6-7.1 18.7-17 22.8C10.1 40.4 3 32.3 3 21.7V6.5Z"
        fill="#00356B"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path
        d="M20 5.2 33.6 9.2v12.4c0 8.6-5.6 15.3-13.6 18.9-8-3.6-13.6-10.3-13.6-18.9V9.2Z"
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.35"
        strokeWidth="0.8"
      />
      <text
        x="20"
        y="27"
        textAnchor="middle"
        fontFamily="'Cormorant Garamond', Georgia, serif"
        fontWeight="700"
        fontSize="15"
        fill="currentColor"
        letterSpacing="0.5"
      >
        CC
      </text>
      <path d="M12 31.5h16" stroke="currentColor" strokeOpacity="0.6" strokeWidth="0.8" />
    </svg>
  )
}
