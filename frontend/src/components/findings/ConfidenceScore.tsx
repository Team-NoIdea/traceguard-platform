import { formatConfidence } from '@/lib/utils'
import { Progress } from '@/components/ui/Progress'

function confidenceColorClasses(confidence: number | undefined): { text: string; bar: string } {
  if (confidence === undefined) return { text: 'text-text-tertiary', bar: 'bg-text-tertiary' }
  if (confidence >= 0.8) return { text: 'text-success', bar: 'bg-success' }
  if (confidence >= 0.5) return { text: 'text-accent', bar: 'bg-accent' }
  return { text: 'text-medium', bar: 'bg-medium' }
}

export function ConfidenceScore({ confidence, size = 'sm' }: { confidence: number | undefined; size?: 'sm' | 'lg' }) {
  const { text, bar } = confidenceColorClasses(confidence)

  if (size === 'sm') {
    return <span className={`text-[13px] font-semibold tabular-nums ${text}`}>{formatConfidence(confidence)}</span>
  }

  return (
    <div className="w-full max-w-[220px] space-y-2">
      <div className="flex items-baseline justify-between">
        <span className={`font-display text-3xl font-semibold tabular-nums ${text}`}>{formatConfidence(confidence)}</span>
        <span className="text-xs text-text-tertiary">confidence</span>
      </div>
      <Progress value={confidence ? confidence * 100 : 0} colorClassName={bar} label="Confidence score" />
    </div>
  )
}
