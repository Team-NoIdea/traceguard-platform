import { Search, ShieldOff } from 'lucide-react'
import { useState } from 'react'

import { PageContainer } from '@/components/layout/PageContainer'
import { EmptyState } from '@/components/ui/EmptyState'
import { SkeletonRows } from '@/components/ui/Skeleton'
import { FindingTable } from '@/components/findings/FindingTable'
import { DEFAULT_FINDING_FILTERS } from '@/features/findings/types'
import { useFindings } from '@/features/findings/hooks'
import { cn } from '@/lib/utils'
import { SEVERITIES } from '@/types'

const SEVERITY_TABS = ['ALL', ...SEVERITIES] as const
const STATUS_OPTIONS = ['ALL', 'OPEN', 'CONFIRMED', 'FIXED', 'DISMISSED']
const CONFIDENCE_OPTIONS = [
  { label: 'Any confidence', value: 0 },
  { label: '50%+', value: 0.5 },
  { label: '70%+', value: 0.7 },
  { label: '90%+', value: 0.9 },
]

export function Findings() {
  const [filters, setFilters] = useState(DEFAULT_FINDING_FILTERS)
  const { data: records, isLoading } = useFindings(filters)

  return (
    <PageContainer title="Security Findings">
      <div className="mb-5">
        <p className="text-sm text-text-secondary">Findings discovered across analyzed repositories.</p>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          <input
            type="text"
            value={filters.search}
            onChange={(event) => setFilters((f) => ({ ...f, search: event.target.value }))}
            placeholder="Search findings…"
            aria-label="Search findings"
            className="w-full rounded-md border border-border-strong bg-surface-sunken py-2 pl-9 pr-3 text-[13px] text-text-primary placeholder:text-text-tertiary focus:border-accent focus:outline-none"
          />
        </div>

        <select
          value={filters.status}
          onChange={(event) => setFilters((f) => ({ ...f, status: event.target.value }))}
          aria-label="Filter by status"
          className="rounded-md border border-border-strong bg-surface-sunken px-3 py-2 text-[13px] text-text-primary focus:border-accent focus:outline-none"
        >
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {status === 'ALL' ? 'All statuses' : status}
            </option>
          ))}
        </select>

        <select
          value={filters.minConfidence}
          onChange={(event) => setFilters((f) => ({ ...f, minConfidence: Number(event.target.value) }))}
          aria-label="Filter by minimum confidence"
          className="rounded-md border border-border-strong bg-surface-sunken px-3 py-2 text-[13px] text-text-primary focus:border-accent focus:outline-none"
        >
          {CONFIDENCE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="mb-4 flex items-center gap-1 border-b border-border">
        {SEVERITY_TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setFilters((f) => ({ ...f, severity: tab }))}
            className={cn(
              'border-b-2 px-3 py-2 text-[13px] font-medium transition-colors',
              filters.severity === tab
                ? 'border-accent text-text-primary'
                : 'border-transparent text-text-tertiary hover:text-text-secondary',
            )}
          >
            {tab === 'ALL' ? 'All' : tab.charAt(0) + tab.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {isLoading ? (
        <SkeletonRows rows={6} />
      ) : !records || records.length === 0 ? (
        <EmptyState
          icon={<ShieldOff size={18} />}
          title="No findings match your filters"
          description="Try widening your search or clearing a filter."
        />
      ) : (
        <FindingTable records={records} />
      )}
    </PageContainer>
  )
}
