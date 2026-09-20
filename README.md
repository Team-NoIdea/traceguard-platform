# TraceGuard

AI-assisted application security analysis for authorized public Python and JavaScript/TypeScript repositories.

## Run locally

1. Configure `.env` from `.env.example` with Firebase Admin, MongoDB and an optional AI provider.
2. Configure `frontend/.env` from `frontend/.env.example` with the **public Firebase web app** configuration. Never put service-account keys in this file.
3. Provision the analyzer images:

```powershell
./scripts/setup-workers.ps1
```

4. Start the application:

```powershell
docker compose up -d --build
```

Landing: http://localhost:5173/ . Sign-in: http://localhost:5173/login . Dashboard: http://localhost:5173/dashboard . API: http://localhost:8000/docs . Ports are bound to localhost.

The landing preserves the supplied single-footer composition, fonts, exact SVG logo, calibrated video seeking and mobile playback, with TraceGuard copy. Start scan and Sign in open `/login`; the remaining display labels and social icons retain the supplied static design.

## Actual scan flow

`Firebase ID token -> owner-scoped scan job -> pinned Git commit -> Python route discovery -> independent Docker scanners -> bounded research -> normalized evidence -> prioritized report`

- Semgrep: default multi-language rules; real JSON results, including correct source paths.
- CodeQL: creates a database for each detected Python or JavaScript/TypeScript language, then runs the security query suite and parses SARIF code flows.
- Joern: constructs a code property graph using its detected-language frontend and queries input/parameter flows to eval, shell and SQL sinks. These are deliberately narrow heuristic queries, not a complete vulnerability catalog.
- Gitleaks: scans current repository files; secrets and raw matches are discarded from normalized reports. It does not claim full Git history coverage.
- OSV-Scanner: known vulnerabilities in recognized manifests/lockfiles.
- Trivy: filesystem dependency vulnerabilities and infrastructure misconfiguration.
- Runtime: builds root Vite applications and checks their preview server, or launches Flask/FastAPI **inside Docker with network disabled**, establishes actual GET baselines and optionally tries bounded, non-destructive query mutations. No host subprocess imports target code.

Every tool returns `COMPLETED`, `FAILED` or a documented unsupported-runtime `SKIPPED` status. A failed static sensor makes the overall scan incomplete (`FAILED`) while retaining available findings. Missing tools are not silently treated as clean.

The research node collects fresh CodeQL/Joern results and runtime mutations, then correlates the updated evidence. Standalone normalized-JSON workflows cannot collect repository evidence and report that limitation explicitly. Repeated observations are deduplicated. AI explanations and proposals are optional; deterministic reporting works without a model.

## Authentication and persistence

All scan, findings, correlation and fix endpoints require a verified Firebase ID token, including revocation checks. The token UID supplies ownership; clients cannot choose it. Reads filter both persisted and in-memory data by owner. Older scans with no owner are intentionally inaccessible, not assigned to arbitrary users.

MongoDB stores user profiles and scan documents, including sensor evidence and fix attempts. Configured database failures return errors rather than mock results. With MongoDB absent, explicitly unconfigured local development uses an in-memory store; this loses history on restart. Frontend auth fails closed when Firebase is not configured and clears cached data when identity changes.

## Fix validation

The scan details page accepts a model proposal or a reviewed unified diff plus a standalone pytest security regression.

`Original commit -> disposable checkout -> original tests -> regression fails -> apply diff -> Python compilation -> existing tests pass -> regression passes -> same scanner images rescan -> compare`

Only the finding's existing Python source file may change. Test/config changes, traversal, file creation/deletion, modes, renames and binary patches are rejected. Workers have no host mounts, credentials, Docker socket, network or elevated capabilities. Validation never changes the submitted repository, pushes a commit, or opens a PR.

`VERIFIED` requires every check and complete original/post-fix sensor coverage, disappearance of the original finding and no new findings. Missing tests, unavailable analyzers and incomplete coverage prevent verification. This is evidence for a candidate patch, not proof of total security. Legacy `/correlation/validate` compares supplied reports only and cannot independently certify scanner coverage.

## Checks

```powershell
npm --prefix frontend run build
docker compose exec backend python -m pytest -q
```

Tests use isolated fixtures and injected identities; they do not create Firebase users. To run real Docker integration checks without touching your configured database or AI provider:

```powershell
docker compose exec -e AI_PROVIDER=disabled -e OPENROUTER_API_KEY= -e MONGODB_URI= backend python scripts/smoke_scanners.py
docker compose exec -e AI_PROVIDER=disabled -e OPENROUTER_API_KEY= -e MONGODB_URI= backend python scripts/smoke_end_to_end.py
```

The end-to-end fixture replaces only network checkout with a local owned Git snapshot. All scanners, runtime probes, patch application, tests and rescans are real. Test reports are written under ignored `storage/`, not inserted into the dashboard.

## Current limits

- Python Flask/FastAPI only. Runtime entrypoint defaults to `main:app`; change it in New Scan. The trusted runtime image includes common framework/test dependencies. Extend `workers/runtime/Dockerfile` for additional dependencies; submitted setup scripts are never installed on the host.
- The job queue is bounded but process-local: use one API process. Interrupted jobs are not automatically recovered. Production needs durable workers, leases and retention.
- The local orchestrator holds the Docker socket. Target workers never receive it. Deploy the orchestrator on a dedicated machine/VM for hostile multi-tenant workloads; Docker is not a VM security boundary.
- Scanner containers that need public rule/vulnerability databases have network access; target application and validation containers do not. Production should mirror scanner data and enforce egress policy.
- Confidence/correlation are heuristics, not calibrated probabilities. Runtime anomalies alone do not establish exploitability.
- File/output/process/memory/time limits are enforced; Docker volume storage should additionally have host disk quotas in production.
- Model-generated patches and tests are untrusted proposals. Human review is still required before adopting a verified candidate.

## Upstream references

[CodeQL database analysis](https://docs.github.com/en/code-security/reference/code-scanning/codeql/codeql-cli-manual/database-analyze), [Joern](https://github.com/joernio/joern), [Gitleaks](https://github.com/gitleaks/gitleaks), [OSV-Scanner](https://google.github.io/osv-scanner/), [Trivy](https://trivy.dev/).
CodeQL usage is subject to GitHub's applicable terms; this implementation only accepts public GitHub repository URLs.

Vite runtime: `traceguard/node-runtime:local` installs the lockfile with `npm ci --ignore-scripts` in a preparation container, then builds and probes in a separate networkless container using the same disposable volume. This checks build and HTTP behavior, not browser interactions. Verified patch application currently remains Python-only. Missing remote scanner images are pulled automatically; local TraceGuard workers require `scripts/setup-workers.ps1`.
