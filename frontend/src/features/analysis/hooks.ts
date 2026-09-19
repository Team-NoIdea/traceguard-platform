import { useState } from 'react'

import { usePolling } from '@/hooks/usePolling'

import { getScanAnalysis } from './mockData'
import type { Scan } from '@/features/scans/types'
import type { ScanAnalysis } from './types'

/**
 * Derives the pipeline/activity view for a scan. Analysis data is a
 * pure function of the scan (see getScanAnalysis) rather than something
 * fetched independently — there's no separate analysis endpoint, so
 * this hook has no api.ts behind it. While the scan is still running,
 * it re-renders on a short interval so the live progress simulation is
 * actually visible instead of frozen at mount time.
 */
export function useScanAnalysis(scan: Scan | undefined): ScanAnalysis | undefined {
  const [, forceTick] = useState(0)
  const isInFlight = scan?.status === 'RUNNING' || scan?.status === 'QUEUED'

  usePolling(() => forceTick((n) => n + 1), 500, isInFlight)

  if (!scan) return undefined
  return getScanAnalysis(scan)
}
