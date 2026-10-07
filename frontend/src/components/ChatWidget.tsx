import { Fragment, useEffect, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { clearChatHistory, fetchCategories, fetchChatHistory, formatPrice, sendChat } from '../api'
import { useAuth } from '../auth'
import { useChatResults } from '../chatResults'
import { useChatUI } from '../chatUI'
import type { Category, ChatMessage, PageResults } from '../types'
import Crest from './Crest'

/** Render **bold** inside a line of text (no raw HTML, so nothing from the model can inject markup). */
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : part,
  )
}

/** Minimal markdown: paragraphs, "- " bullet lists, and **bold**. */
function RichText({ text }: { text: string }) {
  const blocks: ReactNode[] = []
  let bullets: string[] = []
  const flush = () => {
    if (bullets.length) {
      blocks.push(
        <ul key={`ul${blocks.length}`}>
          {bullets.map((b, i) => (
            <li key={i}>{inline(b)}</li>
          ))}
        </ul>,
      )
      bullets = []
    }
  }
  for (const line of text.split('\n')) {
    const bullet = line.match(/^\s*[-*•]\s+(.*)/)
    if (bullet) {
      bullets.push(bullet[1])
    } else {
      flush()
      if (line.trim()) blocks.push(<p key={`p${blocks.length}`}>{inline(line)}</p>)
    }
  }
  flush()
  return <>{blocks}</>
}

/** "7:42 PM" today, otherwise "Oct 5". Stored times are UTC from SQLite. */
function stamp(at?: string) {
  if (!at) return ''
  const d = new Date(at.includes('T') ? at : `${at.replace(' ', 'T')}Z`)
  if (Number.isNaN(d.getTime())) return ''
  const today = new Date().toDateString() === d.toDateString()
  return today
    ? d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    : d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

const TEASER_KEY = 'cc-concierge-teaser-seen'

export default function ChatWidget() {
  const { user } = useAuth()
  const location = useLocation()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { show: showOnPage } = useChatResults()
  const { open, setOpen, pending, takePending } = useChatUI()
  // Page context sent with every message, so "do you have this in pink?" knows what "this" is.
  const viewingProductId = location.pathname.match(/^\/products\/([^/]+)$/)?.[1] ?? null
  const pageContext = { path: location.pathname, product_id: viewingProductId }

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [restored, setRestored] = useState(0)
  const [input, setInput] = useState('')
  const [waiting, setWaiting] = useState(false)
  const [teaser, setTeaser] = useState(false)
  const [categories, setCategories] = useState<Category[]>([])
  const endRef = useRef<HTMLDivElement>(null)
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  const firstName = user?.first_name ?? user?.name
  const greeting: ChatMessage = {
    role: 'assistant',
    content: user
      ? restored
        ? `Welcome back, ${firstName}! Here's where we left off.`
        : `Good to see you, ${firstName}. I'm your Bulldog Concierge: ask me about any hoodie, size, college, or team and I'll check the stockroom.`
      : "Welcome to Campus Customs. I'm your Bulldog Concierge: ask me about any hoodie, size, college, or team and I'll check the stockroom. Log in and I'll remember our chat next time.",
  }

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => {})
  }, [])

  // Customer memory: load the logged-in shopper's saved chat; guests start fresh.
  // Switching accounts also clears the previous shopper's conversation.
  useEffect(() => {
    setMessages([])
    setRestored(0)
    if (!user) return
    let cancelled = false
    fetchChatHistory()
      .then(({ messages: saved }) => {
        if (cancelled) return
        setMessages(
          saved.map((m) => ({
            role: m.role,
            content: m.content,
            products: m.products,
            pageResults: m.page_results ?? undefined,
            at: m.created_at,
          })),
        )
        setRestored(saved.length)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [user])

  // A one-time, dismissible nudge on a shopper's first visit this session.
  useEffect(() => {
    if (sessionStorage.getItem(TEASER_KEY)) return
    const t = setTimeout(() => setTeaser(true), 3500)
    return () => clearTimeout(t)
  }, [])
  useEffect(() => {
    if (open) dismissTeaser()
  }, [open])
  function dismissTeaser() {
    setTeaser(false)
    sessionStorage.setItem(TEASER_KEY, '1')
  }

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, waiting, open])

  // Questions asked from elsewhere on the site ("Ask the Concierge" buttons, marquee, edits).
  useEffect(() => {
    if (!pending || waiting) return
    takePending()
    void send(pending.text)
  }, [pending, waiting])

  /** Problem 7: put the agent's structured matches on the Products page. */
  function openOnPage(results: PageResults) {
    showOnPage(results)
    if (location.pathname !== '/products') navigate('/products')
  }

  async function handleClear() {
    if (user) await clearChatHistory().catch(() => {})
    setMessages([])
    setRestored(0)
  }

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || waiting) return
    const history = messagesRef.current
    const now = new Date().toISOString()
    setMessages((m) => [...m, { role: 'user', content: text, at: now }])
    setInput('')
    setWaiting(true)
    try {
      const { reply, products, page_results } = await sendChat(text, user ? [] : history, pageContext)
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: reply, products, pageResults: page_results ?? undefined, at: new Date().toISOString() },
      ])
      if (page_results) openOnPage(page_results)
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: (err as Error).message || "Sorry, I couldn't reach the server. Please try again.",
          at: new Date().toISOString(),
        },
      ])
    } finally {
      setWaiting(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    void send(input)
  }

  // Suggested questions that fit the page the shopper is on.
  const category = categories.find((c) => c.slug === params.get('category'))
  const suggestions = viewingProductId
    ? ['Do you have this in pink?', 'Is this in stock in a medium?', 'What colors does this come in?', 'Show me similar styles']
    : category
      ? [`Which ${category.label.toLowerCase()} are under $60?`, `Any navy ${category.label.toLowerCase()}?`, 'What’s in stock in a large?']
      : ['What hoodies do you have?', 'Gift ideas for a Yale parent', 'Gear for The Game vs. Harvard', 'Anything for Branford College?']

  return (
    <div className={`chat-root ${open ? 'is-open' : ''}`}>
      {open && (
        <section className="chat-panel" aria-label="Bulldog Concierge chat">
          <header className="chat-header">
            <div className="concierge">
              <span className="concierge-avatar">
                <Crest size={26} />
                <span className="online-dot" />
              </span>
              <div>
                <div className="chat-title">Bulldog Concierge</div>
                <div className="chat-sub">
                  Campus Customs ·{' '}
                  {user ? `chat saved to ${firstName}’s account` : 'guest chat (not saved)'}
                </div>
              </div>
            </div>
            <div className="chat-actions">
              {messages.length > 0 && (
                <button className="text-btn" onClick={handleClear} title="Delete this conversation">
                  Clear
                </button>
              )}
              <button className="icon-btn" onClick={() => setOpen(false)} aria-label="Close chat">
                ×
              </button>
            </div>
          </header>
          <div className="chat-body">
            {[greeting, ...messages].map((m, i) => (
              <Fragment key={i}>
                {restored > 0 && i === restored + 1 && <div className="chat-divider">New messages</div>}
                <div className={`msg msg-${m.role}`}>
                  {m.role === 'assistant' && (
                    <span className="msg-avatar" aria-hidden>
                      <Crest size={18} />
                    </span>
                  )}
                  <div className="msg-col">
                    <div className={`bubble bubble-${m.role}`}>
                      {m.role === 'assistant' ? <RichText text={m.content} /> : m.content}
                    </div>
                    {m.at && <span className="msg-time">{stamp(m.at)}</span>}
                  </div>
                </div>
                {m.pageResults && (
                  <button className="page-chip" onClick={() => openOnPage(m.pageResults!)}>
                    <span className="spark">✦</span> {m.pageResults.total} × {m.pageResults.title} on the page
                    <span className="page-chip-go">View →</span>
                  </button>
                )}
                {m.products && m.products.length > 0 && (
                  <div className="chat-cards">
                    {m.products.map((p) => (
                      <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-card">
                        <img src={p.image_url} alt={p.name} />
                        <div>
                          <div className="chat-card-name">{p.name}</div>
                          <div className="chat-card-meta">
                            <span className="price">{formatPrice(p.price)}</span> · {p.garment_type}
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </Fragment>
            ))}
            {waiting && (
              <div className="msg msg-assistant">
                <span className="msg-avatar" aria-hidden>
                  <Crest size={18} />
                </span>
                <div className="bubble bubble-assistant stockroom" aria-label="Concierge is checking the stockroom">
                  <span className="paws" aria-hidden>
                    <span>🐾</span>
                    <span>🐾</span>
                    <span>🐾</span>
                  </span>
                  Checking the stockroom…
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>
          <div className="chat-suggest" aria-label="Suggested questions">
            {suggestions.map((s) => (
              <button key={s} className="suggest-chip" onClick={() => void send(s)} disabled={waiting}>
                {s}
              </button>
            ))}
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={viewingProductId ? 'Ask about this item…' : 'Ask the concierge anything…'}
              aria-label="Chat message"
              maxLength={1000}
              autoFocus
            />
            <button className="btn btn-pink send-btn" type="submit" disabled={!input.trim() || waiting} aria-label="Send">
              ↑
            </button>
          </form>
        </section>
      )}

      {!open && teaser && (
        <div className="teaser" role="status">
          <button className="teaser-x" onClick={dismissTeaser} aria-label="Dismiss">
            ×
          </button>
          <button className="teaser-body" onClick={() => setOpen(true)}>
            <strong>Looking for your college’s quarter-zip?</strong>
            <span>I can check sizes and stock in seconds.</span>
          </button>
        </div>
      )}

      <button
        className={`chat-fab ${open ? 'is-open' : ''}`}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open the Bulldog Concierge'}
      >
        {open ? (
          <span className="fab-x">×</span>
        ) : (
          <>
            <span className="fab-ring" aria-hidden />
            <Crest size={22} />
            <span className="fab-label">Ask the Concierge</span>
          </>
        )}
      </button>
    </div>
  )
}
