#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm repo update

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Prometheus + Grafana + Alertmanager. The Helm release is named "monitoring".
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values "$HERE/values-prometheus.yaml"

# OpenCost (cost allocation per namespace/pod)
helm upgrade --install opencost opencost/opencost \
  --namespace monitoring \
  --values "$HERE/values-opencost.yaml"

echo
echo "Done. Check the pods with: kubectl -n monitoring get pods"
