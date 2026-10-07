import type { Category, ChatMessage, ChatResponse, PageContext, Product, SignupInput, StoredMessage, User } from './types'

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

// Problem 9 (B2): the catalogue and category list are fetched once per visit and shared by
// Home, Products, product pages, and the nav, instead of re-downloading on every page.
let productsPromise: Promise<Product[]> | null = null
let categoriesPromise: Promise<Category[]> | null = null

export function fetchProducts(): Promise<Product[]> {
  productsPromise ??= getJson<Product[]>('/api/products').catch((e) => {
    productsPromise = null
    throw e
  })
  return productsPromise
}

export function fetchCategories(): Promise<Category[]> {
  categoriesPromise ??= getJson<Category[]>('/api/categories').catch((e) => {
    categoriesPromise = null
    throw e
  })
  return categoriesPromise
}

export const fetchProduct = (id: string) =>
  getJson<Product>(`/api/products/${encodeURIComponent(id)}`)

/**
 * One chat turn with the PydanticAI agent (POST /api/chat). The session cookie tells it who you are.
 * `history` is only used for guests; logged-in history is loaded from the database on the server.
 */
export async function sendChat(
  message: string,
  history: ChatMessage[],
  pageContext: PageContext,
): Promise<ChatResponse> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      history: history.slice(-12).map((m) => ({
        role: m.role,
        content: m.content,
        product_ids: (m.products ?? []).map((p) => p.product_id),
        page_product_ids: (m.pageResults?.products ?? []).map((p) => p.product_id),
      })),
      page_context: pageContext,
    }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : `${res.status} ${res.statusText}`)
  return data as ChatResponse
}

// ---------- customer memory (logged-in shoppers) ----------

export const fetchChatHistory = () => getJson<{ messages: StoredMessage[] }>('/api/chat/history')

export async function clearChatHistory(): Promise<void> {
  const res = await fetch('/api/chat/history', { method: 'DELETE', credentials: 'same-origin' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
}

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

// ---------- auth (session lives in an HttpOnly cookie set by the backend) ----------

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = data?.detail
    throw new Error(typeof detail === 'string' ? detail : 'Something went wrong. Please try again.')
  }
  return data as T
}

export const authMe = () => getJson<{ user: User | null }>('/api/auth/me')
export const authLogin = (email: string, password: string) =>
  postJson<{ user: User }>('/api/auth/login', { email, password })
export const authSignup = (input: SignupInput) => postJson<{ user: User }>('/api/auth/signup', input)
export const authLogout = () => postJson<{ ok: boolean }>('/api/auth/logout')
