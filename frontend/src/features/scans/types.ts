export type ScanStatus = "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";

export interface Scan {
  scan_id: string;
  repository: string;
  repository_url: string;
  branch: string;
  status: ScanStatus;
  findings_count: number;
  high_risk_count: number;
  started_at: string;
  completed_at?: string;
  commit_sha?: string;
  error?: string;
  fixes?: FixAttempt[];
  framework?: string;
  sensors?: Array<{
    name: string;
    status: "COMPLETED" | "SKIPPED" | "FAILED";
    finding_count: number;
    detail?: string;
    phase?: string;
  }>;
  report?: {
    llm_provider?: string;
    llm_error?: string;
    findings: Array<{
      finding_id: string;
      title?: string;
      patch?: { unified_diff?: string | null; rationale?: string; regression_test?: string | null };
      confidence?: number;
      static_evidence: Array<{ tool?: string; evidence?: { flow?: string[] } }>;
      runtime_evidence: Array<{
        endpoint?: string;
        method?: string;
        evidence?: string;
      }>;
      source_tools?: string[];
    }>;
  };
}

export interface CreateScanInput {
  repository_url: string;
  branch: string;
  authorized: boolean;
  runtime_enabled: boolean;
  runtime_entrypoint?: string;
}

/** Derives an "owner/repo" display name from a GitHub-style URL. */
export function repositoryNameFromUrl(url: string): string {
  const cleaned = url
    .trim()
    .replace(/\.git$/, "")
    .replace(/\/+$/, "");
  const match = cleaned.match(/([^/]+\/[^/]+)$/);
  return match ? match[1] : cleaned || "unknown/repository";
}

export interface FixAttempt {
  fix_id: string;
  finding_id: string;
  status: "RUNNING" | "VERIFIED" | "FAILED" | "NOT_VERIFIED";
  checks: Record<string, boolean>;
  details: string[];
  unified_diff: string;
}
