import { apiClient } from "@/lib/api";

import type { CreateScanInput, Scan } from "./types";

interface BackendScan {
  scan_id: string;
  repository_url: string;
  branch: string;
  status: Scan["status"];
  started_at: string;
  completed_at?: string;
  findings_count: number;
  high_risk_count: number;
  framework?: string;
  sensors?: Scan["sensors"];
  report?: Scan["report"];
}

function toScan(scan: BackendScan): Scan {
  const repository = scan.repository_url
    .replace(/\.git$/, "")
    .replace(/\/$/, "")
    .split("/")
    .slice(-2)
    .join("/");
  return {
    ...scan,
    repository,
    framework: scan.framework,
    sensors: scan.sensors,
    report: scan.report,
  };
}

export async function fetchScans(): Promise<Scan[]> {
  const scans = await apiClient.get<BackendScan[]>("/scans");
  return scans.map(toScan);
}

export async function fetchScanById(scanId: string): Promise<Scan | undefined> {
  try {
    return toScan(await apiClient.get<BackendScan>(`/scans/${scanId}`));
  } catch {
    return undefined;
  }
}

export async function startScan(input: CreateScanInput): Promise<Scan> {
  const scan = await apiClient.post<BackendScan, CreateScanInput>(
    "/scans/run",
    input,
  );
  return toScan(scan);
}
