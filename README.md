# CostPilot

Kubernetes aur GPU workloads ke liye open-source, cost-aware DevOps platform.

**Problem:** Companies apna cloud spend ka bohat bara hissa waste karti hain, aur developers ko deploy karte waqt pata nahi hota ke unki change kitne paise khaye gi.

**Solution:** CostPilot cost ko DevOps workflow ke andar le aata hai:

1. Cluster ka cost aur usage data collect karna (Prometheus + OpenCost)
2. Rightsizing recommendations (Python)
3. Policy guardrails (Kyverno)
4. Pull Request par cost impact comment (GitHub Actions) - roadmap
5. Idle environments ka auto-shutdown - roadmap

## Folder structure

```
cluster/      kind cluster config + setup script
monitoring/   Prometheus, Grafana, OpenCost install
apps/         demo app (jaan boojh kar oversized requests ke sath)
loadtest/     k6 load test
analysis/     rightsizing script (Python)
policies/     Kyverno policies
scripts/      helper scripts
docs/         roadmap aur notes
```

## Requirements

Docker, kubectl, helm, kind, k6, Python 3.10+

## Quick start

```bash
make cluster      # kind cluster banao
make monitoring   # Prometheus + Grafana + OpenCost lagao
make app          # demo app deploy karo
make load         # load test chalao (alag terminal mein)
make analyze      # rightsizing report banao
```

Grafana kholne ke liye: `make grafana` phir http://localhost:3000 (user: admin, password: admin).

## Pehle hafta ka goal

1. `make cluster` aur `make monitoring` chal jayein
2. Demo app deploy ho
3. k6 load test se Grafana mein CPU/memory graphs dikhein
4. `make analyze` se pehli recommendation report aaye

## License

MIT
