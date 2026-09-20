import { Link } from 'react-router-dom'
import { firebaseAuth } from '@/lib/firebase'
import { Bell } from 'lucide-react'
import type { ReactNode } from 'react'

interface HeaderProps {
  title: string
  breadcrumb?: ReactNode
  actions?: ReactNode
}

export function Header({ title, breadcrumb, actions }: HeaderProps) {
  const user = firebaseAuth?.currentUser
  const name = user?.displayName || user?.email || 'Account'
  const initials = name.split(/\s+/).map(part => part[0]).slice(0, 2).join('').toUpperCase()
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-canvas px-6">
      <div className="flex min-w-0 items-center gap-2">
        {breadcrumb && <div className="flex items-center gap-1.5 text-sm text-text-tertiary">{breadcrumb}</div>}
        <h1 className="truncate text-[15px] font-semibold text-text-primary">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        {actions}
        <button
          type="button"
          aria-label="Notifications"
          className="flex h-8 w-8 items-center justify-center rounded-md text-text-secondary transition-colors hover:bg-surface-raised hover:text-text-primary"
        >
          <Bell size={16} />
        </button>
        <Link
          to="/profile"
          className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-raised text-xs font-semibold text-text-secondary"
          aria-label="User profile"
          title={name}
        >
          {initials}
        </Link>
      </div>
    </header>
  )
}
