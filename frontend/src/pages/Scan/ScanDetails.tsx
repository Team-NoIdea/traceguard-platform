import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { CheckCircle2, AlertTriangle, Clock3, Download, GitBranch, RefreshCw, ShieldCheck, ArrowUpRight, LoaderCircle } from "lucide-react";
import { PageContainer } from "@/components/layout/PageContainer";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { SeverityBadge } from "@/components/findings/SeverityBadge";
import { useScan, useStartScan } from "@/features/scans/hooks";
import { FixValidation } from "./FixValidation";

const names: Record<string,string> = {semgrep:"Semgrep",gitleaks:"Gitleaks","osv-scanner":"OSV",trivy:"Trivy",codeql:"CodeQL",joern:"Joern",runtime:"Runtime"};
export function ScanDetails() {
  const { scanId } = useParams<{scanId:string}>();
  const {data:scan,isLoading,error,refetch,isFetching} = useScan(scanId);
  const rerun = useStartScan();
  const navigate = useNavigate();
  const [filter,setFilter] = useState("ALL");
  if (isLoading) return <PageContainer title="Loading scan"><Skeleton className="h-40 w-full" /></PageContainer>;
  if (!scan) return <PageContainer title="Scan unavailable"><p role="alert" className="mb-4 text-critical">{error?.message || "This scan could not be loaded."}</p><Button onClick={() => void refetch()}>Try again</Button></PageContainer>;
  const sensors = scan.sensors || [];
  const findings = scan.report?.findings || [];
  const running = ["RUNNING","QUEUED"].includes(scan.status);
  const completed = sensors.filter(s => s.status === "COMPLETED").length;
  const failed = sensors.filter(s => s.status === "FAILED").length;
  const high = findings.filter(f => ["high","critical"].includes(f.severity?.toLowerCase() || "")).length;
  const filtered = findings.filter(f => filter === "ALL" || f.severity?.toUpperCase() === filter);
  const finishedAt = scan.completed_at ? new Date(scan.completed_at) : null;
  const elapsed = finishedAt ? Math.max(0,Math.round((finishedAt.getTime()-Date.parse(scan.started_at))/1000)) : null;
  const ai = scan.report?.llm_provider;
  function download() {
    const url=URL.createObjectURL(new Blob([JSON.stringify(scan,null,2)],{type:"application/json"}));
    const link=document.createElement("a");link.href=url;link.download=`${scan!.scan_id}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <PageContainer title="Repository scan" breadcrumb={<Link to="/dashboard" className="hover:text-accent">Overview /</Link>} actions={<Button variant="ghost" size="sm" disabled={isFetching} onClick={()=>void refetch()} icon={<RefreshCw size={14}/>}>Refresh</Button>}>
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="rounded-xl border border-border bg-surface p-6">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="min-w-0"><p className="mb-2 text-xs uppercase tracking-widest text-text-tertiary">Repository assessment</p><h2 className="break-all text-2xl font-semibold text-text-primary">{scan.repository}</h2><div className="mt-3 flex flex-wrap gap-4 text-xs text-text-secondary"><span className="flex items-center gap-1"><GitBranch size={13}/>{scan.branch}</span><span>{scan.framework || "Framework not detected"}</span><span className="font-mono">Commit {scan.commit_sha?.slice(0,12) || "pending"}</span></div></div>
          <span role="status" className={`flex items-center gap-2 rounded-full px-3 py-2 text-xs font-medium ${running ? "bg-accent-soft text-accent" : failed || scan.status === "FAILED" ? "bg-critical-soft text-critical" : "bg-success-soft text-success"}`}>{running ? <LoaderCircle size={15} className="animate-spin"/> : failed || scan.status === "FAILED" ? <AlertTriangle size={15}/> : <CheckCircle2 size={15}/>} {scan.status}</span>
        </div>
        <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-border pt-5">
          <Button disabled={running || rerun.isPending} icon={<RefreshCw size={14}/>} onClick={()=>rerun.mutate({repository_url:scan.repository_url,branch:scan.branch,authorized:true,runtime_enabled:scan.runtime_enabled ?? true,runtime_entrypoint:scan.runtime_entrypoint}, {onSuccess:next=>navigate(`/scans/${next.scan_id}`)})}>Run again</Button>
          <Button variant="secondary" icon={<Download size={14}/>} onClick={download}>Export report</Button>
          <a href={scan.repository_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-sm text-text-secondary hover:text-accent">Repository <ArrowUpRight size={14}/></a>
          <span className="ml-auto text-xs text-text-tertiary">{new Date(scan.started_at).toLocaleString()}{elapsed !== null ? ` | ${elapsed}s elapsed` : " | Updates automatically"}</span>
        </div>
        {(scan.error || rerun.error || error) && <p role="alert" className="mt-4 text-sm text-critical">{scan.error || rerun.error?.message || error?.message}</p>}
      </section>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{[["Correlated findings",findings.length],["High / critical",high],["Completed sensor runs",completed],["Failed sensor runs",failed]].map(([label,value])=><Card key={label}><p className="text-xs text-text-secondary">{label}</p><p className="mt-2 text-3xl font-semibold text-text-primary">{value}</p></Card>)}</div>
      {running && <p role="status" className="rounded-lg border border-accent/30 bg-accent-soft p-4 text-sm text-accent">Analysis is in progress. Sensor results appear as each worker finishes; correlated findings appear after report generation.</p>}
      <section><div className="mb-3 flex items-center justify-between"><h2 className="text-base font-semibold text-text-primary">Scanner coverage</h2><span className="text-xs text-text-tertiary">{completed} completed / {sensors.length} reported runs</span></div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{Object.entries(names).map(([key,label])=>{
          const runs=sensors.filter(s=>s.name===key);
          const state=runs.some(s=>s.status==="FAILED")?"FAILED":runs.length?runs[runs.length-1].status:running?"PENDING":"NOT RUN";
          return <Card key={key}><div className="mb-3 flex items-center justify-between"><h3 className="font-semibold text-text-primary">{label}</h3><span className={`text-xs ${state==="FAILED"?"text-critical":state==="COMPLETED"?"text-success":"text-text-tertiary"}`}>{state}</span></div>{runs.length?runs.map((s,i)=><div key={i} className="mt-3 border-t border-border pt-3"><div className="flex justify-between text-xs text-text-secondary"><span className="capitalize">{s.phase || "initial"}</span><span>{s.finding_count} observations | {s.duration_seconds?.toFixed(1) ?? "-"}s</span></div><p className="mt-2 text-xs leading-relaxed text-text-tertiary">{s.detail}</p>{s.image && <details className="mt-2 text-xs text-text-tertiary"><summary className="cursor-pointer">Worker image</summary><p className="mt-1 break-all font-mono">{s.image}</p></details>}</div>):<p className="text-xs text-text-tertiary">{running?"Waiting for this worker's result.":"No result recorded for this scanner."}</p>}</Card>;
        })}</div><p className="mt-3 text-xs text-text-tertiary">Zero findings means no matches under that scanner's rules. Runtime HTTP checks do not cover browser interactions.</p>
      </section>
      <Card><CardHeader><CardTitle>Findings in this scan</CardTitle><span className="text-xs text-text-tertiary">{filtered.length} results</span></CardHeader><div className="mb-4 flex flex-wrap gap-2">{["ALL","CRITICAL","HIGH","MEDIUM","LOW","INFO"].map(severity=><button key={severity} onClick={()=>setFilter(severity)} aria-pressed={filter===severity} className={`rounded-full border px-3 py-1.5 text-xs ${filter===severity?"border-accent/40 bg-accent-soft text-accent":"border-border text-text-secondary hover:bg-surface-raised"}`}>{severity}</button>)}</div>
        <div className="divide-y divide-border">{filtered.map(f=><Link key={f.finding_id} to={`/findings/${f.finding_id}?scan=${encodeURIComponent(scan.scan_id)}`} className="flex items-start justify-between gap-4 py-4 hover:text-accent"><div className="min-w-0"><p className="text-sm font-medium text-text-primary">{f.title}</p><p className="mt-1 break-all font-mono text-xs text-text-tertiary">{f.location?.file || "No source location"}{f.location?.line?`:${f.location.line}`:""}</p><p className="mt-2 text-xs text-text-secondary">{f.source_tools?.join(" + ")} | {f.status || "OPEN"}</p></div><SeverityBadge severity={f.severity || "info"}/></Link>)}</div>{filtered.length===0 && <p className="py-6 text-center text-sm text-text-tertiary">{running?"Waiting for the correlated report.":"No findings match this filter."}</p>}
      </Card>
      <div className="grid gap-5 lg:grid-cols-2"><Card><CardHeader><CardTitle>AI analysis</CardTitle></CardHeader><p className="text-sm text-text-primary">{ai && ai!=="deterministic"?`Provider: ${ai}`:running?"Waiting for scan analysis":"Deterministic analysis"}</p><p className="mt-2 text-xs text-text-tertiary">{scan.report?.llm_error || "Explanations use this scan's collected evidence. Review findings before applying a proposed fix."}</p></Card><Card><CardHeader><CardTitle>Research activity</CardTitle></CardHeader><ul className="space-y-2 text-xs text-text-secondary">{scan.report?.workflow_trace?.length?scan.report.workflow_trace.map((item,i)=><li key={i} className="flex gap-2"><Clock3 size={13} className="mt-0.5 shrink-0"/>{item}</li>):<li>No research trace recorded yet.</li>}</ul></Card></div>
      <Card><CardHeader><CardTitle>Remediation verification</CardTitle><ShieldCheck size={17} className="text-accent"/></CardHeader><p className="mb-4 text-xs text-text-tertiary">Verified patch application currently supports Python source files. JavaScript findings include reviewable analysis; they are not automatically marked fixed.</p>{findings.some(f=>f.location?.file.endsWith(".py")) ? <FixValidation key={scan.scan_id} scan={scan}/> : <p className="text-sm text-text-secondary">Open a finding to review its explanation and remediation guidance.</p>}</Card>
      <p className="break-all font-mono text-xs text-text-tertiary">Scan ID: {scan.scan_id}</p>
    </div>
  </PageContainer>;
}
