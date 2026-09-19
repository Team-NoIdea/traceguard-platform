import { Link } from 'react-router-dom'

import { Badge } from '@/components/ui/Badge'
import type { BadgeTone } from '@/components/ui/Badge'
import { humanizeIdentifier } from '@/lib/utils'
import type { FindingRecord } from '@/features/findings/types'

import { ConfidenceScore } from './ConfidenceScore'
import { SeverityBadge } from './SeverityBadge'

const STATUS_TONE: Record<string, BadgeTone> = {
  OPEN: 'accent',
  CONFIRMED: 'critical',
  FIXED: 'success',
  DISMISSED: 'neutral',
}

function evidenceSourceLabel(record: FindingRecord): string {
  const { finding } = record
  const hasStatic = finding.static_evidence.length > 0
  const hasRuntime = finding.runtime_evidence.length > 0
  if (hasStatic && hasRuntime) return 'Static + Runtime'
  if (hasRuntime) return 'Runtime'
  if (hasStatic) return 'Static'
  return '—'
}

export function FindingTable({ records }: { records: FindingRecord[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full min-w-[880px] border-collapse text-left text-[13px]">
        <thead>
          <tr className="border-b border-border bg-surface-raised text-xs text-text-tertiary">
            <th scope="col" className="px-4 py-2.5 font-medium">
              Finding
            </th>
            <th scope="col" className="px-4 py-2.5 font-medium">
              Severity
            </th>
            <th scope="col" className="px-4 py-2.5 font-medium">
              Confidence
            </th>
            <th scope="col" className="px-4 py-2.5 font-medium">
              Repository
            </th>
            <th scope="col" className="px-4 py-2.5 font-medium">
              Location
            </th>
            <th scope="col" className="px-4 py-2.5 font-medium">
              Evidence
            </th>
            <th scope="col" className="px-4 py-2.5 font-medium">
              Status
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle">
          {records.map((record) => {
            const { finding } = record
            return (
              <tr key={finding.finding_id} className="transition-colors hover:bg-surface-raised">
                <td className="px-4 py-3">
                  <Link to={`/findings/${finding.finding_id}`} className="block">
                    <p className="font-medium text-text-primary hover:text-accent">{finding.title}</p>
                    <p className="mt-0.5 text-xs text-text-tertiary">{humanizeIdentifier(finding.type)}</p>
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <SeverityBadge severity={finding.severity} />
                </td>
                <td className="px-4 py-3">
                  <ConfidenceScore confidence={finding.confidence} />
                </td>
                <td className="px-4 py-3 text-text-secondary">{record.repository}</td>
                <td className="px-4 py-3">
                  <span className="font-mono text-xs text-text-secondary">
                    {finding.location?.file ?? '—'}
                    {finding.location?.line ? `:${finding.location.line}` : ''}
                  </span>
                </td>
                <td className="px-4 py-3 text-text-secondary">{evidenceSourceLabel(record)}</td>
                <td className="px-4 py-3">
                  <Badge tone={STATUS_TONE[finding.status] ?? 'neutral'}>{finding.status}</Badge>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
