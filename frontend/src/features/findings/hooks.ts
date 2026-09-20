import { useQuery } from '@tanstack/react-query'

import { fetchFindingById, fetchFindings } from './api'
import type { FindingFilters } from './types'

export function useFindings(filters: FindingFilters) {
  return useQuery({
    queryKey: ['findings', filters],
    queryFn: () => fetchFindings(filters),
    refetchInterval: 5000,
  })
}

export function useFinding(findingId: string | undefined, scanId?: string) {
  return useQuery({
    queryKey: ['findings', findingId, scanId],
    queryFn: () => fetchFindingById(findingId as string, scanId),
    enabled: Boolean(findingId),
  })
}
