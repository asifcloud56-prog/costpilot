#!/usr/bin/env bash
# Usage: bash cluster/setup.sh [kind-config-file]
# Default config: cluster/kind-config.yaml (3 nodes). For 8 GB laptops use cluster/kind-config-light.yaml.
set -euo pipefail

CONFIG="${1:-$(dirname "$0")/kind-config.yaml}"

for tool in docker kubectl helm kind; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Missing: $tool. Please install it first."; exit 1; }
done

if kind get clusters | grep -q '^costpilot$'; then
  echo "Cluster 'costpilot' already exists."
else
  kind create cluster --config "$CONFIG"
fi

kubectl cluster-info --context kind-costpilot
kubectl get nodes
