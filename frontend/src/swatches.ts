/** Catalogue color names -> swatch fills (Problem 10). Covers all 22 names in the database. */
const SWATCHES: Record<string, string> = {
  'navy blue': '#1c2a4a',
  navy: '#1c2a4a',
  white: '#f7f7f5',
  ivory: '#f4efe2',
  cream: '#efe6cf',
  'heather gray': '#a9a9ad',
  gray: '#8e8e93',
  'light gray': '#c9c9cc',
  'dark heather gray': '#5d5e63',
  'charcoal gray': '#45464b',
  'heather charcoal gray': '#4d4e53',
  'dark heather charcoal': '#3f4045',
  black: '#111114',
  red: '#b3262e',
  blue: '#2f5aa8',
  'royal blue': '#2648a8',
  'light blue': '#8fb6e0',
  yellow: '#e8c33a',
  gold: '#c9a23f',
  green: '#2f6b45',
  'dusty coral': '#d98a7a',
  multicolor: 'conic-gradient(#b3262e, #e8c33a, #2f6b45, #2f5aa8, #b3262e)',
}

export function swatch(color: string): string {
  return SWATCHES[color.toLowerCase()] ?? '#777'
}

/** One swatch per distinct fill, so "navy" and "navy blue" don't show twice. */
export function uniqueSwatches(colors: string[]): { name: string; fill: string }[] {
  const seen = new Set<string>()
  return colors
    .map((name) => ({ name, fill: swatch(name) }))
    .filter((s) => (seen.has(s.fill) ? false : (seen.add(s.fill), true)))
}
