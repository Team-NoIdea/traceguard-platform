export type ScanStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export interface Scan {
  scan_id: string
  repository: string
  repository_url: string
  branch: string
  status: ScanStatus
  findings_count: number
  high_risk_count: number
  started_at: string
  completed_at?: string
}

export interface CreateScanInput {
  repository_url: string
  branch: string
}

/** Derives an "owner/repo" display name from a GitHub-style URL. */
export function repositoryNameFromUrl(url: string): string {
  const cleaned = url.trim().replace(/\.git$/, '').replace(/\/+$/, '')
  const match = cleaned.match(/([^/]+\/[^/]+)$/)
  return match ? match[1] : cleaned || 'unknown/repository'
}
