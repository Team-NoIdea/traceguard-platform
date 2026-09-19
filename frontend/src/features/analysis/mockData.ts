import { LIVE_DEMO_SCAN_ID } from '@/features/scans/mockData'
import type { Scan } from '@/features/scans/types'

import type { AgentActivityEvent, PipelineStage, PipelineStageStatus, ScanAnalysis } from './types'

interface StageDefinition {
  id: string
  name: string
  description: string
  /** How long this stage takes in the live demo simulation. */
  durationMs: number
}

// The six TraceGuard pipeline stages, in order. Shared by every scan's
// analysis view so stage names/descriptions stay identical everywhere.
const STAGE_DEFINITIONS: StageDefinition[] = [
  {
    id: 'repository-analysis',
    name: 'Repository Analysis',
    description: 'Cloning the repository and indexing its structure.',
    durationMs: 1800,
  },
  {
    id: 'static-analysis',
    name: 'Static Analysis',
    description: 'Running Semgrep, CodeQL, and Joern across the codebase.',
    durationMs: 2600,
  },
  {
    id: 'runtime-analysis',
    name: 'Runtime Analysis',
    description: 'Exercising live endpoints with baseline and mutated requests.',
    durationMs: 2800,
  },
  {
    id: 'evidence-correlation',
    name: 'Evidence Correlation',
    description: 'Matching static findings against runtime observations.',
    durationMs: 2000,
  },
  {
    id: 'confidence-assessment',
    name: 'Confidence Assessment',
    description: 'Scoring findings against the evidence that supports each one.',
    durationMs: 1800,
  },
  {
    id: 'ai-security-analysis',
    name: 'AI Security Analysis',
    description: 'Synthesizing static and runtime evidence into a human-readable assessment.',
    durationMs: 3200,
  },
]

const STAGE_BOUNDARIES = STAGE_DEFINITIONS.reduce<number[]>((acc, stage, i) => {
  const previous = i === 0 ? 0 : acc[i - 1]
  acc.push(previous + stage.durationMs)
  return acc
}, [])

const TOTAL_DURATION_MS = STAGE_BOUNDARIES[STAGE_BOUNDARIES.length - 1]

// Agent activity log template, verbatim from the product spec — each
// entry fires once its associated stage (by index into
// STAGE_DEFINITIONS) completes, except the last, which intentionally
// never completes in Phase 1 (remediation generation isn't built yet).
const ACTIVITY_TEMPLATE: Array<{ id: string; label: string; stageIndex: number; completesWithStage: boolean }> = [
  { id: 'activity-repo', label: 'Repository structure analyzed', stageIndex: 0, completesWithStage: true },
  { id: 'activity-static', label: 'Static analyzer identified 3 potential findings', stageIndex: 1, completesWithStage: true },
  { id: 'activity-runtime-exec', label: 'Runtime test executed against /api/users', stageIndex: 2, completesWithStage: true },
  { id: 'activity-runtime-anomaly', label: 'Runtime anomaly detected', stageIndex: 2, completesWithStage: true },
  { id: 'activity-correlated', label: 'Evidence correlated with static finding', stageIndex: 3, completesWithStage: true },
  { id: 'activity-ai', label: 'AI analyst reviewing evidence', stageIndex: 5, completesWithStage: true },
  { id: 'activity-remediation', label: 'Remediation generation pending', stageIndex: 5, completesWithStage: false },
]

function stageStatusAt(elapsedMs: number, index: number): PipelineStageStatus {
  const start = index === 0 ? 0 : STAGE_BOUNDARIES[index - 1]
  const end = STAGE_BOUNDARIES[index]
  if (elapsedMs >= end) return 'completed'
  if (elapsedMs >= start) return 'active'
  return 'pending'
}

function buildStages(statuses: PipelineStageStatus[], startedAtMs: number): PipelineStage[] {
  return STAGE_DEFINITIONS.map((def, i) => {
    const status = statuses[i]
    const timestamp = status === 'completed' || status === 'failed' ? new Date(startedAtMs + STAGE_BOUNDARIES[i]).toISOString() : undefined
    return { id: def.id, name: def.name, description: def.description, status, timestamp }
  })
}

/** Live, time-derived analysis for the scan New Scan just created — a
 * pure function of elapsed wall-clock time, so it re-derives correctly
 * on every render/refetch with no separate timer state to manage. */
function buildLiveAnalysis(scan: Scan): ScanAnalysis {
  const startedAtMs = new Date(scan.started_at).getTime()
  const elapsedMs = Date.now() - startedAtMs

  const stageStatuses = STAGE_DEFINITIONS.map((_, i) => stageStatusAt(elapsedMs, i))
  const pipeline = buildStages(stageStatuses, startedAtMs)

  const activity: AgentActivityEvent[] = ACTIVITY_TEMPLATE.map((item) => {
    const stageStatus = stageStatuses[item.stageIndex]
    let status: AgentActivityEvent['status'] = 'pending'
    if (item.completesWithStage && stageStatus === 'completed') status = 'completed'
    else if (stageStatus === 'active' || stageStatus === 'completed') status = item.completesWithStage ? 'active' : 'pending'
    return { id: item.id, label: item.label, status }
  })

  const isComplete = elapsedMs >= TOTAL_DURATION_MS

  return {
    scan_id: scan.scan_id,
    pipeline,
    activity,
    summary: isComplete
      ? { total_findings: 12, high_confidence: 3, runtime_confirmed: 5, static_only: 4 }
      : undefined,
  }
}

function completedActivity(upTo: number): AgentActivityEvent[] {
  return ACTIVITY_TEMPLATE.map((item, i) => ({
    id: item.id,
    label: item.label,
    status: i < upTo ? 'completed' : 'pending',
  }))
}

// Fixed snapshots for the pre-seeded dashboard scans — authored once,
// not time-derived, since they represent a specific point/outcome in
// the pipeline rather than something the user is actively watching.
const FIXED_ANALYSES: Record<string, ScanAnalysis> = {
  'scan-8f21ac': {
    scan_id: 'scan-8f21ac',
    pipeline: buildStages(['completed', 'completed', 'completed', 'completed', 'completed', 'completed'], Date.now() - 6.1 * 60 * 60 * 1000),
    activity: completedActivity(6),
    summary: { total_findings: 3, high_confidence: 2, runtime_confirmed: 2, static_only: 1 },
  },
  'scan-3d9c11': {
    scan_id: 'scan-3d9c11',
    pipeline: buildStages(['completed', 'completed', 'completed', 'completed', 'active', 'pending'], Date.now() - 0.2 * 60 * 60 * 1000),
    activity: completedActivity(5),
  },
  'scan-b02e77': {
    scan_id: 'scan-b02e77',
    pipeline: buildStages(['completed', 'completed', 'failed', 'pending', 'pending', 'pending'], Date.now() - 75 * 60 * 60 * 1000),
    activity: [
      { id: 'activity-repo', label: 'Repository structure analyzed', status: 'completed' },
      { id: 'activity-static', label: 'Static analyzer identified 1 potential finding', status: 'completed' },
      { id: 'activity-runtime-fail', label: 'Runtime analysis failed — target environment unreachable', status: 'failed' },
    ],
  },
  'scan-queued-01': {
    scan_id: 'scan-queued-01',
    pipeline: buildStages(['pending', 'pending', 'pending', 'pending', 'pending', 'pending'], Date.now()),
    activity: [{ id: 'activity-queued', label: 'Waiting for an available scan worker', status: 'pending' }],
  },
}

export function getScanAnalysis(scan: Scan): ScanAnalysis {
  if (scan.scan_id === LIVE_DEMO_SCAN_ID) return buildLiveAnalysis(scan)
  return (
    FIXED_ANALYSES[scan.scan_id] ?? {
      scan_id: scan.scan_id,
      pipeline: buildStages(['pending', 'pending', 'pending', 'pending', 'pending', 'pending'], Date.now()),
      activity: [],
    }
  )
}
