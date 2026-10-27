#!/usr/bin/env bash
# Low-memory install. Optional extras via environment variables:
#   GRAFANA=true   also install Grafana (about 300 MB more)
#   OPENCOST=true  also install OpenCost
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
GRAFANA="${GRAFANA:-false}"
OPENCOST="${OPENCOST:-false}"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm repo update

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values "$HERE/values-prometheus-light.yaml" \
  --set grafana.enabled="$GRAFANA"

if [ "$OPENCOST" = "true" ]; then
  helm upgrade --install opencost opencost/opencost \
    --namespace monitoring \
    --values "$HERE/values-opencost.yaml"
fi

echo
echo "Done. Check the pods with: kubectl -n monitoring get pods"
