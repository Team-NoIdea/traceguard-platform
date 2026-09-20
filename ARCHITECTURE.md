# TraceGuard architecture

The scanners are independent evidence sources. The platform owns authentication, orchestration, normalization, correlation, prioritization and candidate-fix validation.

## Trust boundaries

The browser signs in with Firebase. FastAPI verifies the bearer ID token and derives the UID. MongoDB and memory lookups include that UID; unknown and other-user scan IDs both return 404. Public correlation endpoints have also been removed: normalized evidence processing requires a token.

The trusted orchestrator clones only validated public GitHub HTTPS URLs with credential helpers and Git hooks disabled, records the commit SHA, and never imports submitted code. Each scanner gets its own bounded archive in a disposable Docker volume. No repository symlinks or host bind mounts enter target workers. Workers run non-root with read-only rootfs, dropped capabilities, no privilege escalation, memory/CPU/PID limits and timeouts. Cleanup removes only generated container/volume names.

Runtime and test execution use `--network none`; probes run inside that same container against loopback and do not follow redirects. Static tools needing public databases run separately and never receive platform secrets.

## Evidence and research

Fast scanners feed `SecurityFinding` objects. SARIF preserves code flows, Gitleaks drops secret values, and Python AST locations supply function anchors. LangGraph reviews evidence gaps and calls a bounded repository collector for independent CodeQL/Joern analysis and new runtime mutations. Reports expose sensor status, image digest, duration, phase and workflow trace. An unavailable collector is explicitly reported.

AI receives a bounded source context and structured evidence marked as untrusted data. It may explain, propose a diff and propose a regression test; it cannot execute tools, change confidence weights or apply a patch. Provider failure falls back to deterministic reporting. At most 20 findings per report are enriched.

## Candidate patches

The fix endpoint checks ownership and exact commit provenance, rejects unsafe diff paths and serializes validation. Original tests must pass; a supplied regression must fail before the patch. The diff is applied in a disposable worker, followed by compilation, existing tests and the regression. A separate disposable checkout receives the same validated diff for a rescan with original scanner image digests. Incomplete coverage, persistence or new findings prevents `VERIFIED`.

The original scan remains a record of the original code. Fix attempts are separate candidates stored on the scan; nothing is pushed to the source repository.

## Deployment limits

The bounded thread queue is for one local API process, not a distributed production scheduler. Add durable job storage/recovery, independently provisioned worker VMs, audit/retention policies, disk quotas and mirrored scanner databases before multi-tenant deployment. Runtime images must be explicitly provisioned with project dependencies. Static analysis supports Python and JavaScript/TypeScript; runtime covers Flask/FastAPI and root Vite apps. Vite dependency preparation disables lifecycle scripts; build and HTTP probes run separately with networking disabled. Verified remediation remains Python-only.
