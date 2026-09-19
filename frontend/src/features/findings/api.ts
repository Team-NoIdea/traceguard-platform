import { mockFindingRecords } from './mockData'
import type { FindingFilters, FindingRecord } from './types'

/**
 * Mock data-access layer for findings.
 *
 * Phase 2 replaces the bodies of these two functions with real calls
 * through `apiClient` (see src/lib/api.ts) — callers (the hooks in
 * ./hooks.ts) don't change, since the exported shape (async function
 * returning the same types) stays identical.
 */

const MOCK_LATENCY_MS = 350

function delay<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

export async function fetchFindings(filters: FindingFilters): Promise<FindingRecord[]> {
  const search = filters.search.trim().toLowerCase()

  const filtered = mockFindingRecords.filter((record) => {
    const { finding } = record

    if (filters.severity !== 'ALL' && finding.severity !== filters.severity) return false
    if (filters.status !== 'ALL' && finding.status !== filters.status) return false
    if ((finding.confidence ?? 0) < filters.minConfidence) return false

    if (search.length > 0) {
      const haystack = `${finding.title} ${finding.type} ${record.repository} ${finding.location?.file ?? ''}`.toLowerCase()
      if (!haystack.includes(search)) return false
    }

    return true
  })

  return delay(filtered)
}

export async function fetchFindingById(findingId: string): Promise<FindingRecord | undefined> {
  const record = mockFindingRecords.find((item) => item.finding.finding_id === findingId)
  return delay(record)
}
