import type { ButtonHTMLAttributes, ReactNode } from 'react'

import { cn } from '@/lib/utils'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  icon?: ReactNode
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    'bg-accent text-[#03181d] hover:bg-accent-strong disabled:hover:bg-accent border border-transparent font-medium',
  secondary:
    'bg-surface-raised text-text-primary hover:bg-surface border border-border-strong disabled:hover:bg-surface-raised',
  ghost: 'bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-raised border border-transparent',
  danger: 'bg-transparent text-critical border border-critical/40 hover:bg-critical-soft',
}

const SIZE_CLASSES: Record<Size, string> = {
  sm: 'h-8 px-3 text-[13px] gap-1.5',
  md: 'h-9 px-4 text-sm gap-2',
}

export function Button({ variant = 'primary', size = 'md', icon, className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-md transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer',
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className,
      )}
      {...props}
    >
      {icon}
      {children}
    </button>
  )
}
