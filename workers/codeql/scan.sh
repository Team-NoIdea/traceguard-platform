#!/bin/sh
set -eu
codeql database create /workspace/out/codeql-db --language=python --source-root=/workspace/src --threads=2 --ram=2048
suite=/opt/codeql-packs/codeql/python-queries/1.8.10/codeql-suites/python-security-and-quality.qls
if [ "${1:-}" = research ]; then suite=/opt/codeql-packs/codeql/python-queries/1.8.10/codeql-suites/python-security-extended.qls; fi
codeql database analyze /workspace/out/codeql-db "$suite" --search-path=/opt/codeql-packs --format=sarif-latest --output=/workspace/out/results.json --threads=2 --ram=2048
