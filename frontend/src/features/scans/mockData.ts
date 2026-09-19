import { mockFindingRecords } from '@/features/findings/mockData'

import type { CreateScanInput, Scan } from './types'
import { repositoryNameFromUrl } from './types'

const hoursAgo = (h: number) => new Date(Date.now() - h * 60 * 60 * 1000).toISOString()

function countsForScan(scanId: string) {
  const records = mockFindingRecords.filter((r) => r.scan_id === scanId)
  const highRisk = records.filter((r) => r.finding.severity === 'CRITICAL' || r.finding.severity === 'HIGH')
  return { findings_count: records.length, high_risk_count: highRisk.length }
}

const seedScans: Scan[] = [
  {
    scan_id: 'scan-8f21ac',
    repository: 'acme/payment-api',
    repository_url: 'https://github.com/acme/payment-api',
    branch: 'main',
    status: 'COMPLETED',
    started_at: hoursAgo(6.5),
    completed_at: hoursAgo(6.1),
    ...countsForScan('scan-8f21ac'),
  },
  {
    scan_id: 'scan-3d9c11',
    repository: 'team-noidea/demo-api',
    repository_url: 'https://github.com/team-noidea/demo-api',
    branch: 'develop',
    status: 'RUNNING',
    started_at: hoursAgo(0.2),
    ...countsForScan('scan-3d9c11'),
  },
  {
    scan_id: 'scan-b02e77',
    repository: 'example/flask-app',
    repository_url: 'https://github.com/example/flask-app',
    branch: 'main',
    status: 'FAILED',
    started_at: hoursAgo(75),
    completed_at: hoursAgo(74.9),
    ...countsForScan('scan-b02e77'),
  },
  {
    scan_id: 'scan-queued-01',
    repository: 'octocat/sample-service',
    repository_url: 'https://github.com/octocat/sample-service',
    branch: 'main',
    status: 'QUEUED',
    started_at: hoursAgo(0.02),
    findings_count: 0,
    high_risk_count: 0,
  },
]

/** Mutable in-memory store simulating a backend for the duration of the session. */
const scanStore = new Map<string, Scan>(seedScans.map((scan) => [scan.scan_id, scan]))

// The fixed demo scan id New Scan always creates, per product spec — a
// resubmission just restarts its clock so the progress screen replays.
export const LIVE_DEMO_SCAN_ID = 'mock-scan-001'

export const LIVE_SCAN_DURATION_MS = 14_200

function ensureLiveScanExists(): Scan {
  const existing = scanStore.get(LIVE_DEMO_SCAN_ID)
  if (existing) return existing

  const created: Scan = {
    scan_id: LIVE_DEMO_SCAN_ID,
    repository: 'your-org/your-repo',
    repository_url: 'https://github.com/your-org/your-repo',
    branch: 'main',
    status: 'RUNNING',
    findings_count: 0,
    high_risk_count: 0,
    started_at: new Date().toISOString(),
  }
  scanStore.set(LIVE_DEMO_SCAN_ID, created)
  return created
}

export function listMockScans(): Scan[] {
  // Keep the live demo scan's derived status fresh whenever the list is read.
  const live = scanStore.get(LIVE_DEMO_SCAN_ID)
  if (live) refreshLiveScanStatus(live)

  return [...scanStore.values()].sort(
    (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime(),
  )
}

export function getMockScanById(scanId: string): Scan | undefined {
  if (scanId === LIVE_DEMO_SCAN_ID) {
    const scan = ensureLiveScanExists()
    refreshLiveScanStatus(scan)
    return scan
  }
  return scanStore.get(scanId)
}

function refreshLiveScanStatus(scan: Scan): void {
  const elapsed = Date.now() - new Date(scan.started_at).getTime()
  if (elapsed >= LIVE_SCAN_DURATION_MS && scan.status !== 'COMPLETED') {
    scan.status = 'COMPLETED'
    scan.completed_at = new Date(new Date(scan.started_at).getTime() + LIVE_SCAN_DURATION_MS).toISOString()
    scan.findings_count = 12
    scan.high_risk_count = 3
  }
}

export function createMockScan(input: CreateScanInput): Scan {
  const scan: Scan = {
    scan_id: LIVE_DEMO_SCAN_ID,
    repository: repositoryNameFromUrl(input.repository_url),
    repository_url: input.repository_url,
    branch: input.branch,
    status: 'RUNNING',
    findings_count: 0,
    high_risk_count: 0,
    started_at: new Date().toISOString(),
    completed_at: undefined,
  }
  scanStore.set(LIVE_DEMO_SCAN_ID, scan)
  return scan
}
