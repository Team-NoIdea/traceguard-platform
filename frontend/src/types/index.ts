/**
 * Domain types mirroring the TraceGuard backend's normalized finding
 * schema (schemas/finding.py). Field names are kept identical to the
 * backend on purpose — do not rename them without updating both sides.
 */

export interface Location {
  file: string
  line?: number
  function?: string
}

export interface Evidence {
  source?: string
  sink?: string
  flow: string[]
  description?: string
}

export interface StaticEvidence {
  tool: string
  rule_id?: string
  location?: Location
  evidence?: Evidence
}

export interface RuntimeEvidence {
  endpoint: string
  method?: string
  baseline_status?: number
  mutated_status?: number
  evidence: string
  function?: string
  type?: string
}

export type FindingStatus = 'OPEN' | 'CONFIRMED' | 'DISMISSED' | 'FIXED'

export interface SecurityFinding {
  finding_id: string
  title: string
  type: string
  severity: string
  cwe: string[]
  location?: Location
  confidence?: number
  static_evidence: StaticEvidence[]
  runtime_evidence: RuntimeEvidence[]
  source_tools: string[]
  status: string
  explanation?: string
  remediation?: string
}

export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export const SEVERITIES: Severity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
