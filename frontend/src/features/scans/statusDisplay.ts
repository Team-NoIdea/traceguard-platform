import type { IndicatorTone } from '@/components/ui/StatusIndicator'

import type { ScanStatus } from './types'

export const SCAN_STATUS_DISPLAY: Record<ScanStatus, { label: string; tone: IndicatorTone }> = {
  QUEUED: { label: 'Queued', tone: 'neutral' },
  RUNNING: { label: 'Running', tone: 'accent' },
  COMPLETED: { label: 'Completed', tone: 'success' },
  FAILED: { label: 'Failed', tone: 'critical' },
}
