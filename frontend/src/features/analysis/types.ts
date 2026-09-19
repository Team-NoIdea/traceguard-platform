export type PipelineStageStatus = 'completed' | 'active' | 'pending' | 'failed'

export interface PipelineStage {
  id: string
  name: string
  description: string
  status: PipelineStageStatus
  timestamp?: string
}

export type ActivityStatus = 'completed' | 'active' | 'pending' | 'failed'

export interface AgentActivityEvent {
  id: string
  label: string
  status: ActivityStatus
}

export interface ScanSummary {
  total_findings: number
  high_confidence: number
  runtime_confirmed: number
  static_only: number
}

export interface ScanAnalysis {
  scan_id: string
  pipeline: PipelineStage[]
  activity: AgentActivityEvent[]
  /** Undefined while the scan hasn't reached a state with real counts yet. */
  summary?: ScanSummary
}
