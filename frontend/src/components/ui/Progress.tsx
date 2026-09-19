import { cn } from '@/lib/utils'

interface ProgressProps {
  value: number
  max?: number
  colorClassName?: string
  trackClassName?: string
  className?: string
  label?: string
}

export function Progress({
  value,
  max = 100,
  colorClassName = 'bg-accent',
  trackClassName = 'bg-surface-raised',
  className,
  label,
}: ProgressProps) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100))

  return (
    <div
      className={cn('h-1.5 w-full overflow-hidden rounded-full', trackClassName, className)}
      role="progressbar"
      aria-valuenow={Math.round(percent)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div
        className={cn('h-full rounded-full transition-[width] duration-500 ease-out', colorClassName)}
        style={{ width: `${percent}%` }}
      />
    </div>
  )
}
