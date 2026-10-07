import { createContext, useCallback, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { PageResults } from './types'

/** Search results the chat agent put on the page. Lives above the router so it survives navigation. */
interface ChatResultsState {
  results: PageResults | null
  /** Bumps on every new result set so the cards re-animate. */
  version: number
  show: (results: PageResults) => void
  clear: () => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<PageResults | null>(null)
  const [version, setVersion] = useState(0)

  const show = useCallback((r: PageResults) => {
    setResults(r)
    setVersion((v) => v + 1)
  }, [])
  const clear = useCallback(() => setResults(null), [])

  return (
    <ChatResultsContext.Provider value={{ results, version, show, clear }}>{children}</ChatResultsContext.Provider>
  )
}

export function useChatResults() {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
