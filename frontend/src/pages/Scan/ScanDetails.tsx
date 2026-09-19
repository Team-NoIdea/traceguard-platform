import { AlertOctagon, CheckCircle2, Circle, GitBranch, Hash, ShieldCheck } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageContainer } from '@/components/layout/PageContainer'
import { Skeleton } from '@/components/ui/Skeleton'
import { StatusIndicator } from '@/components/ui/StatusIndicator'
import { useScanAnalysis } from '@/features/analysis/hooks'
import type { PipelineStageStatus, ActivityStatus } from '@/features/analysis/types'
import { SCAN_STATUS_DISPLAY } from '@/features/scans/statusDisplay'
import { useScan } from '@/features/scans/hooks'

function StageIcon({ status }: { status: PipelineStageStatus }) {
  if (status === 'completed') return <CheckCircle2 size={18} className="text-success" />
  if (status === 'active') return <Circle size={18} className="fill-accent-soft text-accent animate-pulse" />
  if (status === 'failed') return <AlertOctagon size={18} className="text-critical" />
  return <Circle size={18} className="text-text-tertiary" />
}

function ActivityIcon({ status }: { status: ActivityStatus }) {
  if (status === 'completed') return <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-success" />
  if (status === 'active') return <Circle size={14} className="mt-0.5 shrink-0 fill-accent-soft text-accent animate-pulse" />
  if (status === 'failed') return <AlertOctagon size={14} className="mt-0.5 shrink-0 text-critical" />
  return <Circle size={14} className="mt-0.5 shrink-0 text-text-tertiary" />
}

export function ScanDetails() {
  const { scanId } = useParams<{ scanId: string }>()
  const navigate = useNavigate()
  const { data: scan, isLoading } = useScan(scanId)
  const analysis = useScanAnalysis(scan)

  if (isLoading) {
    return (
      <PageContainer title="Scan Details">
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </PageContainer>
    )
  }

  if (!scan) {
    return (
      <PageContainer title="Scan Details">
        <EmptyState
          icon={<AlertOctagon size={18} />}
          title="Unable to load scan"
          description="This scan doesn't exist or is no longer available."
          action={
            <Button size="sm" variant="secondary" onClick={() => navigate('/')}>
              Back to Overview
            </Button>
          }
        />
      </PageContainer>
    )
  }

  const statusDisplay = SCAN_STATUS_DISPLAY[scan.status]

  return (
    <PageContainer title="Scan Progress" breadcrumb={<Link to="/" className="hover:text-text-primary">Overview /</Link>}>
      <Card className="mb-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="font-display text-lg font-semibold text-text-primary">{scan.repository}</p>
            <div className="mt-1.5 flex items-center gap-4 text-xs text-text-tertiary">
              <span className="flex items-center gap-1">
                <GitBranch size={12} />
                {scan.branch}
              </span>
              <span className="flex items-center gap-1 font-mono">
                <Hash size={12} />
                {scan.scan_id}
              </span>
            </div>
          </div>
          <StatusIndicator tone={statusDisplay.tone} label={statusDisplay.label} className="text-sm" />
        </div>
      </Card>

      <Card className="mb-5">
        <CardHeader>
          <CardTitle>Analysis Pipeline</CardTitle>
        </CardHeader>

        <ol className="flex flex-col gap-0 lg:flex-row lg:items-start lg:gap-0">
          {analysis?.pipeline.map((stage, i) => (
            <li key={stage.id} className="relative flex flex-1 gap-3 pb-6 lg:flex-col lg:items-center lg:gap-2 lg:pb-0 lg:text-center">
              {i < (analysis.pipeline.length - 1) && (
                <span
                  className="absolute left-[8px] top-6 h-full w-px bg-border lg:left-auto lg:top-[9px] lg:h-px lg:w-full lg:translate-x-[50%]"
                  aria-hidden="true"
                />
              )}
              <span className="relative z-10 shrink-0 bg-surface lg:pb-1">
                <StageIcon status={stage.status} />
              </span>
              <div className="lg:max-w-[140px]">
                <p className="text-[13px] font-medium text-text-primary">{stage.name}</p>
                <p className="mt-0.5 text-xs text-text-tertiary">{stage.description}</p>
              </div>
            </li>
          ))}
        </ol>
      </Card>

      <div className="mb-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Agent Activity</CardTitle>
          </CardHeader>
          <ul className="space-y-2.5">
            {analysis?.activity.map((event) => (
              <li key={event.id} className="flex items-start gap-2 text-[13px]">
                <ActivityIcon status={event.status} />
                <span className={event.status === 'pending' ? 'text-text-tertiary' : 'text-text-secondary'}>{event.label}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Scan Summary</CardTitle>
          </CardHeader>

          {analysis?.summary ? (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="font-display text-2xl font-semibold text-text-primary">{analysis.summary.total_findings}</p>
                <p className="text-xs text-text-tertiary">findings</p>
              </div>
              <div>
                <p className="font-display text-2xl font-semibold text-success">{analysis.summary.high_confidence}</p>
                <p className="text-xs text-text-tertiary">high confidence</p>
              </div>
              <div>
                <p className="font-display text-2xl font-semibold text-accent">{analysis.summary.runtime_confirmed}</p>
                <p className="text-xs text-text-tertiary">runtime-confirmed</p>
              </div>
              <div>
                <p className="font-display text-2xl font-semibold text-text-secondary">{analysis.summary.static_only}</p>
                <p className="text-xs text-text-tertiary">static-only</p>
              </div>
            </div>
          ) : (
            <p className="text-[13px] text-text-tertiary">Summary will be available once analysis completes.</p>
          )}

          <Button className="mt-5 w-full" variant="secondary" icon={<ShieldCheck size={15} />} onClick={() => navigate('/findings')}>
            View Findings
          </Button>
        </Card>
      </div>
    </PageContainer>
  )
}
