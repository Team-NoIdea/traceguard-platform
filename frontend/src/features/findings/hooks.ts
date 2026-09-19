import { useQuery } from '@tanstack/react-query'

import { fetchFindingById, fetchFindings } from './api'
import type { FindingFilters } from './types'

export function useFindings(filters: FindingFilters) {
  return useQuery({
    queryKey: ['findings', filters],
    queryFn: () => fetchFindings(filters),
  })
}

export function useFinding(findingId: string | undefined) {
  return useQuery({
    queryKey: ['findings', findingId],
    queryFn: () => fetchFindingById(findingId as string),
    enabled: Boolean(findingId),
  })
}
