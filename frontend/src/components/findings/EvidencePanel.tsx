import { ArrowDown, ArrowRight } from 'lucide-react'

import type { RuntimeEvidence, StaticEvidence } from '@/types'

/** Renders a source → ... → sink taint chain in code-like styling. */
function FlowChain({ flow }: { flow: string[] }) {
  if (flow.length === 0) {
    return <p className="text-[13px] text-text-tertiary">No taint chain recorded for this evidence.</p>
  }

  return (
    <div className="space-y-0 font-mono text-[13px]">
      {flow.map((step, i) => (
        <div key={`${step}-${i}`}>
          <div className="flex items-center gap-2 rounded-md border border-border-subtle bg-surface-sunken px-3 py-1.5 text-text-primary">
            {step}
          </div>
          {i < flow.length - 1 && (
            <div className="flex justify-center py-0.5 text-text-tertiary">
              <ArrowDown size={13} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export function StaticEvidencePanel({ evidence }: { evidence: StaticEvidence[] }) {
  if (evidence.length === 0) {
    return <p className="text-[13px] text-text-tertiary">No static evidence attached to this finding.</p>
  }

  return (
    <div className="space-y-5">
      {evidence.map((entry, i) => (
        <div key={i} className="space-y-3">
          {entry.evidence && (entry.evidence.flow.length > 0 || entry.evidence.source || entry.evidence.sink) && (
            <FlowChain flow={entry.evidence.flow.length > 0 ? entry.evidence.flow : [entry.evidence.source, entry.evidence.sink].filter((v): v is string => Boolean(v))} />
          )}

          {entry.evidence?.description && <p className="text-[13px] text-text-secondary">{entry.evidence.description}</p>}

          <dl className="grid grid-cols-3 gap-4 border-t border-border-subtle pt-3 text-[13px]">
            <div>
              <dt className="text-text-tertiary">Tool</dt>
              <dd className="mt-0.5 font-medium text-text-primary">{entry.tool}</dd>
            </div>
            <div>
              <dt className="text-text-tertiary">Rule</dt>
              <dd className="mt-0.5 font-mono text-text-primary">{entry.rule_id ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-text-tertiary">Location</dt>
              <dd className="mt-0.5 font-mono text-text-primary">
                {entry.location ? `${entry.location.file}${entry.location.line ? `:${entry.location.line}` : ''}` : '—'}
              </dd>
            </div>
          </dl>
        </div>
      ))}
    </div>
  )
}

export function RuntimeEvidencePanel({ evidence }: { evidence: RuntimeEvidence[] }) {
  if (evidence.length === 0) {
    return <p className="text-[13px] text-text-tertiary">No runtime evidence attached to this finding.</p>
  }

  return (
    <div className="space-y-5">
      {evidence.map((entry, i) => (
        <div key={i} className="space-y-3">
          <div className="flex items-center gap-2 font-mono text-[13px] text-text-primary">
            <span className="rounded bg-surface-raised px-1.5 py-0.5 text-[11px] font-semibold text-accent">
              {entry.method ?? 'GET'}
            </span>
            {entry.endpoint}
          </div>

          <div className="flex items-center gap-3 rounded-md border border-border-subtle bg-surface-sunken px-3 py-2.5 text-[13px]">
            <div className="flex-1">
              <p className="text-text-tertiary">Baseline</p>
              <p className="mt-0.5 font-mono font-medium text-text-primary">{entry.baseline_status ?? '—'}</p>
            </div>
            <ArrowRight size={14} className="shrink-0 text-text-tertiary" />
            <div className="flex-1">
              <p className="text-text-tertiary">Mutated</p>
              <p
                className={`mt-0.5 font-mono font-medium ${
                  entry.mutated_status && entry.baseline_status && entry.mutated_status !== entry.baseline_status
                    ? 'text-critical'
                    : 'text-text-primary'
                }`}
              >
                {entry.mutated_status ?? '—'}
              </p>
            </div>
          </div>

          <dl className="grid grid-cols-2 gap-4 text-[13px]">
            <div>
              <dt className="text-text-tertiary">Evidence</dt>
              <dd className="mt-0.5 text-text-primary">{entry.evidence}</dd>
            </div>
            <div>
              <dt className="text-text-tertiary">Function</dt>
              <dd className="mt-0.5 font-mono text-text-primary">{entry.function ?? '—'}</dd>
            </div>
          </dl>
        </div>
      ))}
    </div>
  )
}
