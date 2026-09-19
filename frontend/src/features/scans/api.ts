import { createMockScan, getMockScanById, listMockScans } from './mockData'
import type { CreateScanInput, Scan } from './types'

const MOCK_LATENCY_MS = 300

function delay<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

export async function fetchScans(): Promise<Scan[]> {
  return delay(listMockScans())
}

export async function fetchScanById(scanId: string): Promise<Scan | undefined> {
  return delay(getMockScanById(scanId))
}

export async function startScan(input: CreateScanInput): Promise<Scan> {
  // Real submit-and-navigate flow, just against an in-memory mock
  // instead of a POST to the backend.
  return delay(createMockScan(input), 500)
}
