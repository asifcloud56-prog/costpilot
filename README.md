# CostPilot

**Open-source, cost-aware DevOps tooling for Kubernetes.**
CostPilot finds over-provisioned workloads, recommends right-sized resource requests, and (on the roadmap) brings cost feedback directly into the pull-request workflow.

> **Status: work in progress.** The data pipeline and the right-sizing report are working. Validation, the pull-request cost bot and policy guardrails are in development. See the [roadmap](#roadmap).

---

## Why this project exists

Cloud cost is now an engineering problem, not just a finance problem, yet developers rarely see what a change costs before it ships.

- Organizations waste roughly 27-35% of their cloud spend (Flexera, 2025; industry estimates).
- Kubernetes clusters average about 10% CPU utilization, and about 70% of requested resources go unused (CAST AI 2025 benchmark of 2,100+ organizations).
- GPU utilization is reported as low as 5% (CAST AI, 2026).
- It takes an average of 31 days to identify cloud waste (Harness, 2025).

CostPilot's goal is to shorten that loop: measure real usage, compare it with what teams request, and surface the gap where developers already work.

## What it does today

1. **Collects data:** Prometheus and kube-state-metrics run on a local Kubernetes (kind) cluster. A low-memory profile runs on an 8 GB laptop; Grafana and OpenCost are optional.
2. **Generates load:** a demo service plus a k6 load test produce realistic usage patterns.
3. **Recommends right-sizing:** a Python script reads p95 CPU and memory usage from Prometheus, adds a 30% safety margin and compares it against the requested resources.
4. **Validates the change:** it applies the recommendation, repeats the load test and produces a before/after table.

## First result (controlled test)

The demo app was deliberately deployed with oversized requests (0.4 CPU, 512 MiB memory per pod, 2 pods) to check that the pipeline detects waste and that applying its recommendation is safe. The same 7-minute k6 load test (up to 20 virtual users) ran before and after.

**Step 1: detection.** Observed p95 usage plus a 30% safety margin versus what was requested:

| Resource (per pod) | Requested | Recommended | Waste |
|---|---|---|---|
| CPU | 0.40 core | ~0.19 core | ~51-54% |
| Memory | 512 MiB | ~63-70 MiB | ~86-88% |

**Step 2: validation.** Recommendations applied (200m CPU, 80 MiB memory), then the same load test repeated:

| Metric | Before | After | Change |
|---|---|---|---|
| CPU requests per pod | 0.40 | 0.20 | -50% |
| Memory requests per pod (MiB) | 512 | 80 | -84% |
| Latency avg (ms) | 33.9 | 38.6 | +14% |
| Latency p95 (ms) | 84.4 | 102.0 | +21% |
| Failed requests | 0.00% | 0.00% | none |
| Requests served | 4,239 | 4,218 | similar |

No pod restarts or OOM kills occurred during the "after" run. Full table: [`results/comparison.md`](results/comparison.md).

**What this shows:** reserved memory dropped 84% and CPU 50% with no failed requests, at the cost of a small p95 latency increase that stays far below the 500 ms threshold. Part of that increase may come from the lower CPU limit (1 core to 0.8 core); this has not been isolated yet.

> **Note:** this is a controlled experiment on a single-node test cluster with intentionally oversized requests, one workload and one run each. It shows the detection and validation pipeline works. It is not a claim about savings in a real production environment. Repeated runs and validation on real and public workloads are on the roadmap.

## Architecture

```
  k6 load test
       |
       v
  Demo app (Flask) ---> Kubernetes (kind: 1 control-plane + 2 workers)
                                 |
              +------------------+------------------+
              |                  |                  |
         Prometheus           OpenCost            Grafana
              |
              v
   analysis/rightsize.py  --->  report.csv (requested vs recommended)
```

## Tech stack

Kubernetes (kind), Docker, Helm, Prometheus, Grafana, OpenCost, Python (pandas, requests), k6, Kyverno, GitHub Actions, Trivy.

## Repository layout

```
cluster/      kind cluster config and setup script
monitoring/   Helm values and install script (Prometheus, Grafana, OpenCost)
apps/         demo application and Kubernetes manifests
loadtest/     k6 load test script
analysis/     right-sizing report, apply and compare scripts (Python)
results/      before/after measurements
policies/     Kyverno policy (audit mode)
docs/         roadmap and notes
.github/      CI workflow (build and image scan)
```

## Quick start

**Requirements:** Docker, kubectl, Helm, kind, k6, Python 3.10+ (Linux, macOS, or Windows with WSL2).

```bash
git clone https://github.com/asifcloud56-prog/costpilot.git
cd costpilot

python3 -m venv .venv
source .venv/bin/activate

make cluster       # create the kind cluster
make monitoring    # install Prometheus, Grafana, OpenCost
make app           # build and deploy the demo app
```

Then open three terminals:

```bash
make grafana       # Grafana at http://localhost:3000  (admin / admin, local use only)
make prometheus    # Prometheus at http://localhost:9090
make load          # 7-minute k6 load test
```

After the load test finishes:

```bash
make analyze       # prints the right-sizing table and saves analysis/report.csv
```

Clean up with `make clean`.

> The default Grafana password (`admin`) is for local learning only. Do not use these values on a shared or public cluster.

## Low-memory profile (8 GB laptops)

The default setup (3 nodes plus Prometheus, Grafana, Alertmanager, node-exporter and OpenCost) needs roughly 5-6 GB of RAM. On an 8 GB machine use the light profile: a single node, with only Prometheus and kube-state-metrics, which is all the right-sizing workflow needs.

```bash
make cluster-light
make monitoring-light            # add GRAFANA=true if you want dashboards
make app
```

## Before/after validation

The key question is whether the recommendations are safe: do requests drop while performance stays the same? The workflow below answers it (run `make prometheus` in a second terminal for step 3).

```bash
make reset-app     # 1. deploy the original, oversized requests
make load-before   # 2. load test + snapshot of requests
make analyze       # 3. right-sizing report
make apply         # 4. apply the recommended requests and wait for the rollout
make load-after    # 5. same load test again
make compare       # 6. before/after table -> results/comparison.md
```

Results are written to `results/comparison.md`.

## Roadmap

- [x] Local cluster with Prometheus, Grafana and OpenCost
- [x] Demo workload and k6 load test
- [x] Right-sizing report (v0.1)
- [x] Before/after validation tooling (`make apply`, `make compare`); first real run pending
- [ ] Pull-request cost bot (GitHub Action that comments the estimated cost impact of a change)
- [ ] Policy guardrails with Kyverno (audit mode, then enforce)
- [ ] Automatic shutdown of idle environments
- [ ] Evaluation on public cluster traces (Google, Alibaba) and real workloads
- [ ] GPU utilization analysis
- [ ] GreenOps: energy and carbon estimates (Kepler)
- [ ] Public results page and write-up

## Limitations

- Recommendations use a simple percentile-plus-headroom rule. There is no forecasting model yet.
- Cost figures from OpenCost use default pricing on the local cluster, not real cloud pricing.
- Results so far come from a single small demo workload.

## Contributing

Issues and pull requests are welcome. This is an early-stage learning and portfolio project, so feedback on the approach is especially appreciated.

## License

MIT. See [LICENSE](LICENSE).
