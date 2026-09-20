import { FileCode2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { formatRelativeTime } from '@/lib/utils'
import type { FindingRecord } from '@/features/findings/types'

import { ConfidenceScore } from './ConfidenceScore'
import { SeverityBadge } from './SeverityBadge'

export function FindingCard({ record }: { record: FindingRecord }) {
  const { finding } = record

  return (
    <Link
      to={`/findings/${finding.finding_id}?scan=${encodeURIComponent(record.scan_id)}`}
      className="flex items-center gap-4 rounded-md border border-transparent px-3 py-3 transition-colors hover:border-border hover:bg-surface-raised"
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-medium text-text-primary">{finding.title}</p>
          <SeverityBadge severity={finding.severity} />
        </div>
        <div className="mt-1 flex items-center gap-1.5 text-xs text-text-tertiary">
          <FileCode2 size={12} />
          <span className="truncate font-mono">
            {record.repository} | {finding.location?.file}
            {finding.location?.line ? `:${finding.location.line}` : ''}
          </span>
        </div>
        <p className="mt-1 text-xs text-text-tertiary">{finding.source_tools.join(" + ")} | Scan {record.scan_id.slice(-8)}</p>
      </div>

      <ConfidenceScore confidence={finding.confidence} />

      <span className="w-16 shrink-0 text-right text-xs text-text-tertiary">{formatRelativeTime(record.detected_at)}</span>
    </Link>
  )
}
