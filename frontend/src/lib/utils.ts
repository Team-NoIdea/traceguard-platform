/**
 * Joins class names, dropping falsy values. Deliberately minimal (no
 * `clsx`/`tailwind-merge` dependency) — this project's class lists are
 * short enough that a conflict-resolving merge isn't needed.
 */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ')
}

/** Formats a 0..1 confidence score as a whole-number percentage string. */
export function formatConfidence(confidence: number | undefined): string {
  if (confidence === undefined) return '—'
  return `${Math.round(confidence * 100)}%`
}

/** Formats an ISO timestamp as a short relative time ("3m ago", "2h ago"). */
export function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  const now = Date.now()
  const diffSeconds = Math.max(0, Math.round((now - then) / 1000))

  if (diffSeconds < 60) return 'just now'
  const diffMinutes = Math.round(diffSeconds / 60)
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.round(diffHours / 24)
  if (diffDays < 30) return `${diffDays}d ago`
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

/** Title-cases a SCREAMING_SNAKE or snake_case identifier for display. */
export function humanizeIdentifier(value: string): string {
  return value
    .toLowerCase()
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(' ')
}

/** Truncates a file path from the left, keeping the most relevant (right) end. */
export function truncatePathStart(value: string, maxLength = 40): string {
  if (value.length <= maxLength) return value
  return `…${value.slice(value.length - maxLength + 1)}`
}
