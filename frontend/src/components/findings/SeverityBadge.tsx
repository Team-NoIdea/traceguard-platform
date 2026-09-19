import { Badge } from '@/components/ui/Badge'

import { severityTone } from './severity'

export function SeverityBadge({ severity, className }: { severity: string; className?: string }) {
  return (
    <Badge tone={severityTone(severity)} className={className}>
      {severity.toUpperCase()}
    </Badge>
  )
}
