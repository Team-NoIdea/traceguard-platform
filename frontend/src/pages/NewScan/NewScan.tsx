import { ShieldAlert } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useStartScan } from "@/features/scans/hooks";

export function NewScan() {
  const navigate = useNavigate();
  const startScan = useStartScan();

  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [authorized, setAuthorized] = useState(false);
  const [runtimeEnabled, setRuntimeEnabled] = useState(true);
  const [entrypoint, setEntrypoint] = useState("main:app");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!repositoryUrl.trim()) return;

    try {
    const scan = await startScan.mutateAsync({
      repository_url: repositoryUrl.trim(),
      branch: branch.trim() || "main",
      authorized,
      runtime_enabled: runtimeEnabled,
      runtime_entrypoint: entrypoint,
    });
    navigate(`/scans/${scan.scan_id}`);
    } catch { /* Mutation error is displayed below. */ }
  };

  return (
    <PageContainer title="New Scan">
      <div className="mx-auto max-w-xl">
        <div className="mb-6">
          <h2 className="font-display text-xl font-semibold text-text-primary">
            Start a Security Scan
          </h2>
          <p className="mt-1 text-sm text-text-secondary">
            Analyze a repository using static analysis, runtime testing, and
            AI-assisted evidence correlation.
          </p>
        </div>

        <Card>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="repository-url"
                className="mb-1.5 block text-[13px] font-medium text-text-primary">
                Repository URL
              </label>
              <input
                id="repository-url"
                type="text"
                required
                value={repositoryUrl}
                onChange={(event) => setRepositoryUrl(event.target.value)}
                placeholder="https://github.com/example/flask-app"
                className="w-full rounded-md border border-border-strong bg-surface-sunken px-3 py-2 font-mono text-[13px] text-text-primary placeholder:text-text-tertiary focus:border-accent focus:outline-none"
              />
            </div>

            <div>
              <label
                htmlFor="branch"
                className="mb-1.5 block text-[13px] font-medium text-text-primary">
                Branch
              </label>
              <input
                id="branch"
                type="text"
                value={branch}
                onChange={(event) => setBranch(event.target.value)}
                placeholder="main"
                className="w-full rounded-md border border-border-strong bg-surface-sunken px-3 py-2 font-mono text-[13px] text-text-primary placeholder:text-text-tertiary focus:border-accent focus:outline-none"
              />
            </div>

            <label className="flex items-start gap-2 rounded-md border border-border-subtle bg-surface-sunken px-3 py-2.5 text-xs text-text-secondary">
              <ShieldAlert size={14} className="mt-0.5 shrink-0 text-medium" />
              <input
                type="checkbox"
                checked={authorized}
                onChange={(event) => setAuthorized(event.target.checked)}
              />
              <span> I own this repository or am authorized to test it.</span>
            </label>

            <label className="flex items-start gap-2 text-xs text-text-secondary">
              <input
                type="checkbox"
                checked={runtimeEnabled}
                onChange={(event) => setRuntimeEnabled(event.target.checked)}
              />
              <span>
                Run isolated HTTP checks for Flask/FastAPI, or build and check a Vite app.
              </span>
            </label>

            {runtimeEnabled && <label className="block text-sm">Python entrypoint (Vite is detected automatically)<input value={entrypoint} onChange={e=>setEntrypoint(e.target.value)} placeholder="main:app" className="mt-2 w-full rounded border border-border p-2"/></label>}
            {startScan.error && <p role="alert" className="text-sm text-critical">{startScan.error.message}</p>}
            <div className="flex items-center gap-3 pt-1">
              <Button
                type="submit"
                disabled={
                  startScan.isPending || !repositoryUrl.trim() || !authorized
                }>
                {startScan.isPending ? "Starting Scanâ€¦" : "Start Scan"}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => navigate(-1)}>
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </PageContainer>
  );
}
