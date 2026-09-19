import { cn } from '@/lib/utils'

export type IndicatorTone = 'success' | 'accent' | 'neutral' | 'critical' | 'warning'

const TONE_DOT_CLASSES: Record<IndicatorTone, string> = {
  success: 'bg-success',
  accent: 'bg-accent animate-pulse',
  neutral: 'bg-text-tertiary',
  critical: 'bg-critical',
  warning: 'bg-medium',
}

const TONE_TEXT_CLASSES: Record<IndicatorTone, string> = {
  success: 'text-success',
  accent: 'text-accent',
  neutral: 'text-text-secondary',
  critical: 'text-critical',
  warning: 'text-medium',
}

interface StatusIndicatorProps {
  tone: IndicatorTone
  label: string
  className?: string
}

export function StatusIndicator({ tone, label, className }: StatusIndicatorProps) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-sm font-medium', TONE_TEXT_CLASSES[tone], className)}>
      <span className={cn('h-1.5 w-1.5 rounded-full', TONE_DOT_CLASSES[tone])} />
      {label}
    </span>
  )
}
