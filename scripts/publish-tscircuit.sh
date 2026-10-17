#!/usr/bin/env bash
# Keep full engineering sources in GitHub; publish only viewer and CAM files.
set -euo pipefail
project_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$project_root"
python3 scripts/verify-publish-readiness.py --prototype
/workspace/.routing-venv/bin/python scripts/verify-bottom-markings.py
python3 scripts/verify-jlcpcb-review.py
python3 scripts/verify-public-model-assets.py
python3 scripts/publish-lean-tscircuit.py "$@"
