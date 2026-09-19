import type { BadgeTone } from '@/components/ui/Badge'

const SEVERITY_TONE: Record<string, BadgeTone> = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
}

export function severityTone(severity: string): BadgeTone {
  return SEVERITY_TONE[severity.toUpperCase()] ?? 'neutral'
}
