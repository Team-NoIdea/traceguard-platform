import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

export type BadgeTone = 'neutral' | 'accent' | 'success' | 'critical' | 'high' | 'medium' | 'low'

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: 'bg-surface-raised text-text-secondary border-border',
  accent: 'bg-accent-soft text-accent border-accent/30',
  success: 'bg-success-soft text-success border-success/30',
  critical: 'bg-critical-soft text-critical border-critical/30',
  high: 'bg-high-soft text-high border-high/30',
  medium: 'bg-medium-soft text-medium border-medium/30',
  low: 'bg-low-soft text-low border-low/30',
}

interface BadgeProps {
  tone?: BadgeTone
  children: ReactNode
  className?: string
  icon?: ReactNode
}

export function Badge({ tone = 'neutral', children, className, icon }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium leading-5',
        TONE_CLASSES[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  )
}
