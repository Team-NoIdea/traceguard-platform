import { AlertOctagon, CheckCircle2, Circle, FileCode2, GitPullRequest, Sparkles, Wand2 } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageContainer } from '@/components/layout/PageContainer'
import { Skeleton } from '@/components/ui/Skeleton'
import { ConfidenceScore } from '@/components/findings/ConfidenceScore'
import { RuntimeEvidencePanel, StaticEvidencePanel } from '@/components/findings/EvidencePanel'
import { SeverityBadge } from '@/components/findings/SeverityBadge'
import { useFinding } from '@/features/findings/hooks'
import { humanizeIdentifier } from '@/lib/utils'
import type { SecurityFinding } from '@/types'

interface ChecklistItem {
  label: string
  met: boolean
}

function buildEvidenceChecklist(finding: SecurityFinding): ChecklistItem[] {
  const primarySink = finding.static_evidence.find((e) => e.evidence?.sink)?.evidence?.sink
  const hasSource = finding.static_evidence.some((e) => e.evidence?.source)
  const hasSink = finding.static_evidence.some((e) => e.evidence?.sink)
  const hasRuntime = finding.runtime_evidence.length > 0
  const staticFunction = finding.location?.function ?? finding.static_evidence.find((e) => e.location?.function)?.location?.function
  const runtimeMatchesFunction = finding.runtime_evidence.some((r) => r.function && r.function === staticFunction)

  return [
    { label: 'User-controlled input detected', met: hasSource },
    { label: primarySink ? `Input reaches ${primarySink}` : 'Input reaches a sensitive sink', met: hasSink },
    { label: 'Runtime mutation triggered a server-side anomaly', met: hasRuntime },
    { label: 'Runtime evidence matches target function', met: runtimeMatchesFunction },
    { label: 'Static and runtime evidence correlated', met: hasRuntime && finding.static_evidence.length > 0 },
  ]
}

function buildConfidenceContributions(finding: SecurityFinding): string[] {
  const contributions: string[] = []
  if (finding.static_evidence.length > 0) contributions.push('Static evidence')
  if (finding.runtime_evidence.length > 0) contributions.push('Runtime confirmation')
  if (finding.static_evidence.some((e) => e.evidence?.source && e.evidence?.sink)) contributions.push('Source-to-sink flow')
  const staticFunction = finding.location?.function
  if (staticFunction && finding.runtime_evidence.some((r) => r.function === staticFunction)) contributions.push('Function correlation')
  return contributions
}

interface DiffLine {
  type: 'add' | 'remove' | 'context'
  text: string
}

function parseRemediation(remediation: string | undefined): { diffLines: DiffLine[]; explanation: string } {
  if (!remediation) return { diffLines: [], explanation: '' }

  const blocks = remediation.split('\n\n')
  const diffBlock = blocks[0] ?? ''
  const explanation = blocks.slice(1).join('\n\n')

  const diffLines: DiffLine[] = diffBlock
    .split('\n')
    .filter((line) => line.trim().length > 0)
    .map((line) => ({
      type: line.startsWith('+') ? 'add' : line.startsWith('-') ? 'remove' : 'context',
      text: line.replace(/^[-+]\s?/, ''),
    }))

  return { diffLines, explanation }
}

const DIFF_LINE_CLASSES: Record<DiffLine['type'], string> = {
  add: 'bg-success-soft text-success before:content-["+"]',
  remove: 'bg-critical-soft text-critical before:content-["-"]',
  context: 'text-text-secondary before:content-["_"]',
}

export function FindingDetails() {
  const { findingId } = useParams<{ findingId: string }>()
  const navigate = useNavigate()
  const { data: record, isLoading } = useFinding(findingId)

  if (isLoading) {
    return (
      <PageContainer title="Finding Details">
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </PageContainer>
    )
  }

  if (!record) {
    return (
      <PageContainer title="Finding Details">
        <EmptyState
          icon={<AlertOctagon size={18} />}
          title="Finding not found"
          description="This finding doesn't exist or may have been removed."
          action={
            <Button size="sm" variant="secondary" onClick={() => navigate('/findings')}>
              Back to Findings
            </Button>
          }
        />
      </PageContainer>
    )
  }

  const { finding } = record
  const checklist = buildEvidenceChecklist(finding)
  const contributions = buildConfidenceContributions(finding)
  const { diffLines, explanation: remediationExplanation } = parseRemediation(finding.remediation)

  return (
    <PageContainer title={finding.title} breadcrumb={<Link to="/findings" className="hover:text-text-primary">Findings /</Link>}>
      <Card className="mb-5">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="font-display text-xl font-semibold text-text-primary">{finding.title}</h2>
              <SeverityBadge severity={finding.severity} />
              <Badge tone="neutral">{finding.status}</Badge>
              {finding.cwe.map((id) => (
                <Badge key={id} tone="neutral">
                  {id}
                </Badge>
              ))}
            </div>
            <p className="mt-1 text-sm text-text-secondary">{humanizeIdentifier(finding.type)}</p>

            {finding.location && (
              <div className="mt-3 flex items-center gap-1.5 font-mono text-[13px] text-text-secondary">
                <FileCode2 size={14} />
                {finding.location.file}
                {finding.location.function && <span className="text-text-tertiary"> · {finding.location.function}()</span>}
                {finding.location.line && <span className="text-text-tertiary"> · line {finding.location.line}</span>}
              </div>
            )}
          </div>

          <ConfidenceScore confidence={finding.confidence} size="lg" />
        </div>
      </Card>

      <Card className="mb-5">
        <CardHeader>
          <CardTitle>Why This Was Flagged</CardTitle>
        </CardHeader>
        <ul className="space-y-2">
          {checklist.map((item) => (
            <li key={item.label} className="flex items-center gap-2 text-[13px]">
              {item.met ? (
                <CheckCircle2 size={15} className="shrink-0 text-success" />
              ) : (
                <Circle size={15} className="shrink-0 text-text-tertiary" />
              )}
              <span className={item.met ? 'text-text-primary' : 'text-text-tertiary line-through'}>{item.label}</span>
            </li>
          ))}
        </ul>
      </Card>

      <div className="mb-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Static Evidence</CardTitle>
          </CardHeader>
          <StaticEvidencePanel evidence={finding.static_evidence} />
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Runtime Evidence</CardTitle>
          </CardHeader>
          <RuntimeEvidencePanel evidence={finding.runtime_evidence} />
        </Card>
      </div>

      <div className="mb-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Confidence</CardTitle>
          </CardHeader>
          <ConfidenceScore confidence={finding.confidence} size="lg" />
          <ul className="mt-4 space-y-1.5 border-t border-border-subtle pt-4">
            {contributions.length === 0 && <li className="text-[13px] text-text-tertiary">No corroborating evidence yet.</li>}
            {contributions.map((label) => (
              <li key={label} className="flex items-center gap-2 text-[13px] text-text-secondary">
                <span className="text-success">+</span>
                {label}
              </li>
            ))}
          </ul>
        </Card>

        <Card className="border-accent/20">
          <CardHeader>
            <CardTitle>
              <span className="flex items-center gap-1.5">
                <Sparkles size={14} className="text-accent" />
                AI Security Analysis
              </span>
            </CardTitle>
            <Badge tone="accent">Mock analysis</Badge>
          </CardHeader>
          {finding.explanation ? (
            <p className="text-[13px] leading-relaxed text-text-secondary">{finding.explanation}</p>
          ) : (
            <p className="text-[13px] text-text-tertiary">
              TraceGuard's AI analyst will synthesize static and runtime evidence here.
            </p>
          )}
          <p className="mt-3 text-xs text-text-tertiary">
            Placeholder for Phase 2 — will be generated by TraceGuard's LangGraph-based AI analyst.
          </p>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recommended Remediation</CardTitle>
        </CardHeader>

        {diffLines.length > 0 ? (
          <>
            <pre className="overflow-x-auto rounded-md border border-border-subtle bg-surface-sunken p-3 font-mono text-[13px] leading-6">
              {diffLines.map((line, i) => (
                <div key={i} className={`whitespace-pre px-2 before:mr-2 before:inline-block before:w-3 before:text-text-tertiary ${DIFF_LINE_CLASSES[line.type]}`}>
                  {line.text}
                </div>
              ))}
            </pre>
            {remediationExplanation && (
              <p className="mt-3 text-[13px] text-text-secondary">
                <span className="font-medium text-text-primary">Why this fix: </span>
                {remediationExplanation}
              </p>
            )}
          </>
        ) : (
          <p className="text-[13px] text-text-tertiary">No remediation suggestion is available for this finding yet.</p>
        )}

        <div className="mt-4 flex items-center gap-3 border-t border-border-subtle pt-4">
          <Button size="sm" variant="secondary" icon={<Wand2 size={14} />} disabled title="Coming in Phase 2">
            Apply Fix
          </Button>
          <Button size="sm" variant="secondary" icon={<GitPullRequest size={14} />} disabled title="Coming in Phase 2">
            Create Pull Request
          </Button>
          <span className="text-xs text-text-tertiary">Coming in Phase 2</span>
        </div>
      </Card>
    </PageContainer>
  )
}
