export interface StockLevel {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_file_path: string
  image_url: string
  price: number
  category: string
  /** size -> quantity, XS..XXL (from GET /api/products) */
  stock?: Record<string, number>
  total_stock?: number
  inventory?: StockLevel[]
}

/** One aisle of the shop (Problem 9): GET /api/categories. */
export interface Category {
  slug: string
  label: string
  count: number
  image_url: string
}

/** A product card from the chat API (built server-side from the database). */
export interface ProductCardData {
  product_id: string
  name: string
  garment_type: string
  price: number
  image_url: string
  description: string
  colors: string[]
}

/** Problem 7 API contract: search results the agent asks the website to show on the page. */
export interface PageResults {
  title: string
  total: number
  products: ProductCardData[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: ProductCardData[]
  pageResults?: PageResults
  /** ISO or SQLite UTC timestamp, shown under the bubble */
  at?: string
}

/** Where the shopper is when they send a message (Problem 8). */
export interface PageContext {
  path: string
  product_id: string | null
}

/** A saved message from GET /api/chat/history (logged-in shoppers only). */
export interface StoredMessage {
  role: 'user' | 'assistant'
  content: string
  products: ProductCardData[]
  page_results: PageResults | null
  created_at: string
}

export interface ChatResponse {
  reply: string
  products: ProductCardData[]
  page_results: PageResults | null
}

export interface User {
  id: number
  first_name: string | null
  last_name: string | null
  name: string
  email: string
}

export interface SignupInput {
  first_name: string
  last_name: string
  email: string
  password: string
}
