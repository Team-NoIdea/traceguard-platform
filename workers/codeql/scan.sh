#!/bin/sh
set -eu
exec python3 /opt/traceguard/scan.py "$@"
