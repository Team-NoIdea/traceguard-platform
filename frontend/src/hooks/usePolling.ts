import { useEffect, useRef } from 'react'

/**
 * Calls `callback` every `intervalMs` while `enabled` is true.
 *
 * Used for UI that needs to re-render on a timer independent of any
 * data fetch — e.g. the scan progress screen, where pipeline state is
 * derived client-side from elapsed time rather than re-fetched. For
 * polling an actual endpoint (re-fetching data while a job runs),
 * prefer TanStack Query's `refetchInterval` instead (see
 * features/scans/hooks.ts) — this hook is for driving re-renders, not
 * data fetching.
 */
export function usePolling(callback: () => void, intervalMs: number, enabled = true): void {
  const callbackRef = useRef(callback)

  // Keep the ref current after each render (in an effect, not during
  // render itself — mutating a ref during render is unsafe under
  // concurrent rendering).
  useEffect(() => {
    callbackRef.current = callback
  })

  useEffect(() => {
    if (!enabled) return

    const id = window.setInterval(() => callbackRef.current(), intervalMs)
    return () => window.clearInterval(id)
  }, [intervalMs, enabled])
}
