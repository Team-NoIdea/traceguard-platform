$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    foreach ($image in @('semgrep/semgrep@sha256:34ab619bf1391a24bfda3f05debd0d8a6ce3093c2d5f9d39cfc00f83c1397823','zricethezav/gitleaks:v8.24.3','ghcr.io/google/osv-scanner:v2.2.2','aquasec/trivy:0.69.3')) {
        docker pull $image
        if ($LASTEXITCODE -ne 0) { throw "Failed to pull $image" }
    }
    foreach ($worker in @('runtime','codeql','joern')) {
        docker build -t "traceguard/${worker}:local" "workers/$worker"
        if ($LASTEXITCODE -ne 0) { throw "Failed to build $worker" }
    }
} finally { Pop-Location }
