import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

import { Header } from './Header'

interface PageContainerProps {
  title: string
  breadcrumb?: ReactNode
  actions?: ReactNode
  children: ReactNode
  className?: string
}

export function PageContainer({ title, breadcrumb, actions, children, className }: PageContainerProps) {
  return (
    <div className="flex h-screen flex-1 flex-col overflow-hidden">
      <Header title={title} breadcrumb={breadcrumb} actions={actions} />
      <main className={cn('flex-1 overflow-y-auto px-6 py-6', className)}>{children}</main>
    </div>
  )
}
