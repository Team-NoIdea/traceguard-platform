import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchScanById, fetchScans, startScan } from './api'
import type { CreateScanInput, Scan } from './types'

export function useScans() {
  return useQuery({
    queryKey: ['scans'],
    queryFn: fetchScans,
    refetchInterval: 5000,
  })
}

export function useScan(scanId: string | undefined) {
  return useQuery({
    queryKey: ['scans', scanId],
    queryFn: () => fetchScanById(scanId as string),
    enabled: Boolean(scanId),
    // Poll while the scan is still in flight, same shape Phase 2 will
    // use to poll a real backend job — stop once it settles.
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'RUNNING' || status === 'QUEUED' ? 1500 : false
    },
  })
}

export function useStartScan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: CreateScanInput) => startScan(input),
    onSuccess: (scan: Scan) => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      queryClient.setQueryData(['scans', scan.scan_id], scan)
    },
  })
}
