import type { SecurityFinding } from '@/types'

/**
 * A finding plus the contextual metadata a list/detail view needs but
 * that SecurityFinding itself doesn't carry (it's scoped to one repo's
 * scan in the real backend, not the cross-repo findings inbox this UI
 * shows). Kept as a wrapper rather than fields bolted onto
 * SecurityFinding, so that type stays a 1:1 match with the backend
 * schema.
 */
export interface FindingRecord {
  finding: SecurityFinding
  repository: string
  branch: string
  scan_id: string
  detected_at: string
}

export interface FindingFilters {
  search: string
  severity: string | 'ALL'
  status: string | 'ALL'
  minConfidence: number
}

export const DEFAULT_FINDING_FILTERS: FindingFilters = {
  search: '',
  severity: 'ALL',
  status: 'ALL',
  minConfidence: 0,
}
