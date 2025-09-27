#!/usr/bin/env bash
set -euo pipefail
# run from any directory
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
for svc in auction bid user gateway; do
  python -m grpc_tools.protoc             -I common/protos             --python_out=$svc             --grpc_python_out=$svc             common/protos/auction.proto common/protos/bid.proto common/protos/user.proto
  echo "generated for $svc"
done
