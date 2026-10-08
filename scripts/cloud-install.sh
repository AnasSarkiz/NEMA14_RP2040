#!/usr/bin/env bash
set -euo pipefail
cd /workspace/NEMA14_RP2040
mkdir -p /workspace/.npm-cache /workspace/.config /workspace/.cache
npm ci --legacy-peer-deps --cache /workspace/.npm-cache --no-audit --no-fund
# npm cannot enforce registry integrity on this locked Git dependency; compare its executable sources to the verified upstream commit.
sha256sum --check --status scripts/trace-linter.sha256
python3 -m venv /workspace/.routing-venv
/workspace/.routing-venv/bin/python -m pip install --cache-dir /workspace/.pip-cache -r scripts/requirements-router.txt -r scripts/requirements-manufacturing.txt
# Optional fallback router, pinned and checksum-verified; Java21 is available in this image.
if [ ! -f /workspace/freerouting-2.0.1.jar ]; then
  curl --fail --location --retry 2 https://github.com/freerouting/freerouting/releases/download/v2.0.1/freerouting-2.0.1.jar -o /workspace/freerouting-2.0.1.jar
fi
printf '%s  %s\n' d7fd0f63f52e6d74b0fad6715f87ca9f0ffd7109d66b2a584638000270592ecf /workspace/freerouting-2.0.1.jar | sha256sum --check --status
npm run typecheck
npm run build
npm run shorts
