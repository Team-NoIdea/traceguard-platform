import { apiClient } from "@/lib/api";
import type { FindingFilters, FindingRecord } from "./types";

export async function fetchFindings(
  filters: FindingFilters,
): Promise<FindingRecord[]> {
  const records = await apiClient.get<FindingRecord[]>("/findings");
  const search = filters.search.trim().toLowerCase();
  return records.filter((record) => {
    const { finding } = record;

    if (filters.severity !== "ALL" && finding.severity.toLowerCase() !== filters.severity.toLowerCase())
      return false;
    if (filters.status !== "ALL" && finding.status !== filters.status)
      return false;
    if ((finding.confidence ?? 0) < filters.minConfidence) return false;

    if (search.length > 0) {
      const haystack =
        `${finding.title} ${finding.type} ${record.repository} ${finding.location?.file ?? ""}`.toLowerCase();
      if (!haystack.includes(search)) return false;
    }

    return true;
  });
}

export async function fetchFindingById(
  findingId: string,
): Promise<FindingRecord | undefined> {
  const records = await apiClient.get<FindingRecord[]>("/findings");
  return records.find((record) => record.finding.finding_id === findingId);
}
