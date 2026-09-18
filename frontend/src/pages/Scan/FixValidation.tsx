import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import type { Scan, FixAttempt } from "@/features/scans/types";

export function FixValidation({scan}:{scan:Scan}) {
  const [findingId,setFindingId] = useState("");
  const [diff,setDiff] = useState("");
  const [regression,setRegression] = useState("");
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState("");
  const [result,setResult] = useState<FixAttempt>();
  const client = useQueryClient();
  async function validate() {
    setBusy(true);setError("");
    try {
      setResult(await apiClient.post<FixAttempt>(`/scans/${scan.scan_id}/fixes/validate`,{finding_id:findingId,unified_diff:diff,regression_test:regression}));
      await client.invalidateQueries({queryKey:["scans",scan.scan_id]});
    } catch (e) { setError(e instanceof Error ? e.message : "Validation failed"); }
    finally {setBusy(false);}
  }
  const latest = result ?? scan.fixes?.at(-1);
  return <div className="space-y-4">
    <p className="text-sm text-text-secondary">Review a proposed diff or paste a fix. Validation applies it to a disposable checkout of this scan?s commit, runs tests, and rescans all engines.</p>
    <select aria-label="Finding to fix" className="w-full rounded border border-border bg-surface p-2 text-sm" value={findingId} onChange={e=>{setFindingId(e.target.value);setRegression(scan.report?.findings.find(f=>f.finding_id===e.target.value)?.patch?.regression_test??"");setDiff(scan.report?.findings.find(f=>f.finding_id===e.target.value)?.patch?.unified_diff??"");}}>
      <option value="">Choose a finding</option>{scan.report?.findings.map(f=><option key={f.finding_id} value={f.finding_id}>{f.title}</option>)}
    </select>
    <textarea aria-label="Unified diff" value={diff} onChange={e=>setDiff(e.target.value)} rows={8} placeholder="Paste a unified diff for the finding?s Python file" className="w-full rounded border border-border bg-surface-sunken p-3 font-mono text-xs"/>
    <textarea aria-label="Security regression test" value={regression} onChange={e=>setRegression(e.target.value)} rows={5} placeholder="Standalone pytest regression: must fail on the original code and pass after the fix" className="w-full rounded border border-border bg-surface-sunken p-3 font-mono text-xs"/>
    <button onClick={()=>void validate()} disabled={busy||!findingId||!diff||!regression||["QUEUED","RUNNING"].includes(scan.status)} className="rounded bg-accent px-4 py-2 text-sm text-white disabled:opacity-40">{busy?"Applying, testing and rescanning?":"Validate fix in sandbox"}</button>
    {error&&<p role="alert" className="text-sm text-critical">{error}</p>}
    {latest&&<div className="rounded border border-border p-3 text-sm"><strong>{latest.status.replaceAll("_"," ")}</strong><ul className="mt-2 space-y-1">{Object.entries(latest.checks).map(([name,passed])=><li key={name}>{passed?"PASS":"FAIL"} {name.replaceAll("_"," ")}</li>)}</ul>{latest.details.map((d,i)=><p key={i} className="mt-2 text-text-secondary">{d}</p>)}</div>}
  </div>;
}
