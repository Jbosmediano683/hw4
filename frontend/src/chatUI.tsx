import { createContext, useCallback, useContext, useState } from 'react'
import type { ReactNode } from 'react'

/**
 * Lets any part of the site talk to the chat (Problem 10): "Ask the Concierge" buttons,
 * the college marquee, and curated edits call ask("…") to open the panel and send a question.
 */
interface ChatUIState {
  open: boolean
  setOpen: (open: boolean | ((o: boolean) => boolean)) => void
  /** A question waiting to be sent by the widget; `id` makes repeated identical asks distinct. */
  pending: { text: string; id: number } | null
  ask: (text: string) => void
  takePending: () => void
}

const ChatUIContext = createContext<ChatUIState | null>(null)

export function ChatUIProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [pending, setPending] = useState<ChatUIState['pending']>(null)

  const ask = useCallback((text: string) => {
    setOpen(true)
    setPending({ text, id: Date.now() })
  }, [])
  const takePending = useCallback(() => setPending(null), [])

  return (
    <ChatUIContext.Provider value={{ open, setOpen, pending, ask, takePending }}>{children}</ChatUIContext.Provider>
  )
}

export function useChatUI() {
  const ctx = useContext(ChatUIContext)
  if (!ctx) throw new Error('useChatUI must be used inside <ChatUIProvider>')
  return ctx
}
