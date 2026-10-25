#!/usr/bin/env bash
set -euo pipefail

for tool in docker kubectl helm kind; do
  command -v "$tool" >/dev/null 2>&1 || { echo "Missing: $tool. Please install it first."; exit 1; }
done

if kind get clusters | grep -q '^costpilot$'; then
  echo "Cluster 'costpilot' already exists."
else
  kind create cluster --config "$(dirname "$0")/kind-config.yaml"
fi

kubectl cluster-info --context kind-costpilot
kubectl get nodes
