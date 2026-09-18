import type { Scan } from "@/features/scans/types";
import type { PipelineStage, PipelineStageStatus, ScanAnalysis } from "./types";

/**
 * Derives the pipeline/activity view for a scan. Analysis data is a
 * pure function of the scan (see getScanAnalysis) rather than something
 * fetched independently — there's no separate analysis endpoint, so
 * this hook has no api.ts behind it. While the scan is still running,
 * it re-renders on a short interval so the live progress simulation is
 * actually visible instead of frozen at mount time.
 */
export function useScanAnalysis(
  scan: Scan | undefined,
): ScanAnalysis | undefined {
  if (!scan) return undefined;
  const sensorStatus = new Map(
    (scan.sensors ?? []).map((sensor) => [sensor.name, sensor.status]),
  );
  const statusFor = (names: string[]): PipelineStageStatus => {
    if (names.some((name) => sensorStatus.get(name) === "FAILED"))
      return "failed";
    if (
      scan.status === "COMPLETED" &&
      names.some((name) => sensorStatus.get(name) === "COMPLETED")
    )
      return "completed";
    if (scan.status === "RUNNING") return "active";
    return "pending";
  };
  const pipeline: PipelineStage[] = [
    {
      id: "repository-analysis",
      name: "Repository Analysis",
      description: `Detected ${scan.framework ?? "unknown"} application`,
      status: scan.commit_sha ? "completed" : scan.status === "FAILED" ? "failed" : "active",
    },
    {
      id: "static-analysis",
      name: "Static Analysis",
      description: "Results from configured repository sensors",
      status: statusFor([
        "semgrep",
        "codeql",
        "joern",
        "gitleaks",
        "osv-scanner",
        "trivy",
      ]),
    },
    {
      id: "runtime-analysis",
      name: "Runtime Analysis",
      description: "Networkless Docker baseline and bounded mutations",
      status: statusFor(["runtime"]),
    },
    {
      id: "evidence-correlation",
      name: "Evidence Correlation",
      description: "Merged findings from persisted scan output",
      status: scan.status === "COMPLETED" ? "completed" : "pending",
    },
    {
      id: "confidence-assessment",
      name: "Confidence Assessment",
      description: "Deterministic evidence confidence",
      status: scan.status === "COMPLETED" ? "completed" : "pending",
    },
    {
      id: "ai-security-analysis",
      name: "AI Security Analysis",
      description: "Configured model or deterministic fallback",
      status: scan.status === "COMPLETED" ? "completed" : "pending",
    },
  ];
  const findings = scan.report?.findings ?? [];
  return {
    scan_id: scan.scan_id,
    pipeline,
    activity: pipeline.map((stage) => ({
      id: stage.id,
      label: stage.description,
      status:
        stage.status === "completed"
          ? "completed"
          : stage.status === "failed"
            ? "failed"
            : stage.status === "active"
              ? "active"
              : "pending",
    })),
    summary:
      scan.status === "COMPLETED"
        ? {
            total_findings: scan.findings_count,
            high_confidence: findings.filter(
              (finding) => (finding.confidence ?? 0) >= 0.8,
            ).length,
            runtime_confirmed: findings.filter(
              (finding) => finding.runtime_evidence.length > 0,
            ).length,
            static_only: findings.filter(
              (finding) =>
                finding.static_evidence.length > 0 &&
                finding.runtime_evidence.length === 0,
            ).length,
          }
        : undefined,
  };
}
