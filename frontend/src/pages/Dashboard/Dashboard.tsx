import { AlertTriangle, ArrowRight, Plus, Radar, ShieldCheck, Target } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { PageContainer } from '@/components/layout/PageContainer'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { SkeletonRows } from '@/components/ui/Skeleton'
import { StatusIndicator } from '@/components/ui/StatusIndicator'
import { FindingCard } from '@/components/findings/FindingCard'
import { DEFAULT_FINDING_FILTERS } from '@/features/findings/types'
import { useFindings } from '@/features/findings/hooks'
import { SCAN_STATUS_DISPLAY } from '@/features/scans/statusDisplay'
import { useScans } from '@/features/scans/hooks'
import { formatConfidence, formatRelativeTime } from '@/lib/utils'
import { SEVERITIES } from '@/types'

const SEVERITY_BAR_CLASS: Record<string, string> = {
  CRITICAL: 'bg-critical',
  HIGH: 'bg-high',
  MEDIUM: 'bg-medium',
  LOW: 'bg-low',
}

function StatCard({ label, value, icon: Icon }: { label: string; value: string; icon: typeof Radar }) {
  return (
    <Card className="flex items-center justify-between" padded>
      <div>
        <p className="text-xs text-text-tertiary">{label}</p>
        <p className="mt-1 font-display text-2xl font-semibold text-text-primary">{value}</p>
      </div>
      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-surface-raised text-accent">
        <Icon size={16} />
      </div>
    </Card>
  )
}

export function Dashboard() {
  const navigate = useNavigate()
  const { data: scans, isLoading: scansLoading } = useScans()
  const { data: findings, isLoading: findingsLoading } = useFindings(DEFAULT_FINDING_FILTERS)

  const totalScans = scans?.length ?? 0
  const openFindings = findings?.filter((r) => r.finding.status === 'OPEN').length ?? 0
  const highRiskFindings = findings?.filter((r) => r.finding.severity === 'CRITICAL' || r.finding.severity === 'HIGH').length ?? 0
  const averageConfidence =
    findings && findings.length > 0
      ? findings.reduce((sum, r) => sum + (r.finding.confidence ?? 0), 0) / findings.length
      : undefined

  const severityCounts = SEVERITIES.map((severity) => ({
    severity,
    count: findings?.filter((r) => r.finding.severity === severity).length ?? 0,
  }))
  const maxSeverityCount = Math.max(1, ...severityCounts.map((s) => s.count))

  const recentScans = [...(scans ?? [])].slice(0, 5)
  const recentFindings = [...(findings ?? [])]
    .sort((a, b) => new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime())
    .slice(0, 5)

  return (
    <PageContainer
      title="Security Overview"
      actions={
        <Button size="sm" icon={<Plus size={15} />} onClick={() => navigate('/scans/new')}>
          New Scan
        </Button>
      }
    >
      <div className="mb-6">
        <p className="font-display text-xl font-semibold text-text-primary">TraceGuard</p>
        <p className="text-sm text-text-secondary">AI-assisted application security analysis</p>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Scans" value={String(totalScans)} icon={Radar} />
        <StatCard label="Open Findings" value={String(openFindings)} icon={ShieldCheck} />
        <StatCard label="High Risk Findings" value={String(highRiskFindings)} icon={AlertTriangle} />
        <StatCard label="Average Confidence" value={formatConfidence(averageConfidence)} icon={Target} />
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2" padded={false}>
          <CardHeader className="px-5 pt-5">
            <CardTitle>Recent Scans</CardTitle>
            <Link to="/scans/new" className="text-xs font-medium text-accent hover:underline">
              New scan
            </Link>
          </CardHeader>

          {scansLoading ? (
            <div className="px-5 pb-5">
              <SkeletonRows rows={4} />
            </div>
          ) : recentScans.length === 0 ? (
            <div className="px-5 pb-5">
              <EmptyState icon={<Radar size={18} />} title="No scans yet" description="Start your first scan to see it here." />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] border-collapse text-left text-[13px]">
                <thead>
                  <tr className="border-y border-border text-xs text-text-tertiary">
                    <th scope="col" className="px-5 py-2 font-medium">
                      Repository
                    </th>
                    <th scope="col" className="px-3 py-2 font-medium">
                      Branch
                    </th>
                    <th scope="col" className="px-3 py-2 font-medium">
                      Status
                    </th>
                    <th scope="col" className="px-3 py-2 font-medium">
                      Findings
                    </th>
                    <th scope="col" className="px-3 py-2 font-medium">
                      Last Scanned
                    </th>
                    <th scope="col" className="px-5 py-2 text-right font-medium">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {recentScans.map((scan) => (
                    <tr key={scan.scan_id} className="hover:bg-surface-raised">
                      <td className="px-5 py-2.5 font-medium text-text-primary">{scan.repository}</td>
                      <td className="px-3 py-2.5 font-mono text-xs text-text-secondary">{scan.branch}</td>
                      <td className="px-3 py-2.5">
                        <StatusIndicator tone={SCAN_STATUS_DISPLAY[scan.status].tone} label={SCAN_STATUS_DISPLAY[scan.status].label} />
                      </td>
                      <td className="px-3 py-2.5 text-text-secondary">{scan.findings_count}</td>
                      <td className="px-3 py-2.5 text-text-tertiary">{formatRelativeTime(scan.started_at)}</td>
                      <td className="px-5 py-2.5 text-right">
                        <Link to={`/scans/${scan.scan_id}`} className="text-xs font-medium text-accent hover:underline">
                          View Scan
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Security Overview</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {severityCounts.map(({ severity, count }) => (
              <div key={severity}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="font-medium text-text-secondary">{severity}</span>
                  <span className="tabular-nums text-text-tertiary">{count}</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-raised">
                  <div
                    className={`h-full rounded-full ${SEVERITY_BAR_CLASS[severity]}`}
                    style={{ width: `${(count / maxSeverityCount) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card padded={false}>
        <CardHeader className="px-5 pt-5">
          <CardTitle>Recent Findings</CardTitle>
          <Link to="/findings" className="flex items-center gap-1 text-xs font-medium text-accent hover:underline">
            View all findings
            <ArrowRight size={12} />
          </Link>
        </CardHeader>

        <div className="px-2 pb-3">
          {findingsLoading ? (
            <div className="px-3 pb-2">
              <SkeletonRows rows={4} />
            </div>
          ) : recentFindings.length === 0 ? (
            <div className="px-3 pb-2">
              <EmptyState icon={<ShieldCheck size={18} />} title="No findings yet" description="Findings will appear here once a scan completes." />
            </div>
          ) : (
            recentFindings.map((record) => <FindingCard key={record.finding.finding_id} record={record} />)
          )}
        </div>
      </Card>
    </PageContainer>
  )
}
