#!/usr/bin/env python3
"""CostPilot rightsizing report (v0.1).

Prometheus se har container ka actual CPU/memory usage nikalta hai,
requests se compare karta hai, aur recommendation deta hai.

Pehle terminal mein chalao:  make prometheus
Phir:                        python3 analysis/rightsize.py --namespace demo
"""
import argparse
import sys

import pandas as pd
import requests

HEADROOM = 1.3  # p95 usage par 30% safety margin


def query(prom_url: str, promql: str) -> pd.DataFrame:
    r = requests.get(f"{prom_url}/api/v1/query", params={"query": promql}, timeout=30)
    r.raise_for_status()
    rows = []
    for item in r.json()["data"]["result"]:
        m = item["metric"]
        rows.append(
            {
                "pod": m.get("pod", ""),
                "container": m.get("container", ""),
                "value": float(item["value"][1]),
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--prometheus", default="http://localhost:9090")
    p.add_argument("--namespace", default="demo")
    p.add_argument("--window", default="1h", help="kitne time ka data dekhna hai, jaise 1h, 1d, 7d")
    args = p.parse_args()

    ns, w = args.namespace, args.window

    queries = {
        "cpu_req": f'sum by (pod, container) (kube_pod_container_resource_requests{{namespace="{ns}",resource="cpu",container!=""}})',
        "mem_req": f'sum by (pod, container) (kube_pod_container_resource_requests{{namespace="{ns}",resource="memory",container!=""}})',
        "cpu_p95": f'quantile_over_time(0.95, rate(container_cpu_usage_seconds_total{{namespace="{ns}",container!=""}}[5m])[{w}:1m])',
        "mem_p95": f'quantile_over_time(0.95, container_memory_working_set_bytes{{namespace="{ns}",container!=""}}[{w}])',
    }

    try:
        frames = {k: query(args.prometheus, q).rename(columns={"value": k}) for k, q in queries.items()}
    except requests.RequestException as e:
        print(f"Prometheus se connect nahi hua ({args.prometheus}): {e}")
        print("Pehle 'make prometheus' chalao.")
        return 1

    df = None
    for f in frames.values():
        if f.empty:
            continue
        df = f if df is None else df.merge(f, on=["pod", "container"], how="outer")

    if df is None or df.empty:
        print("Koi data nahi mila. App deploy karo aur load test chalao, phir dobara try karo.")
        return 1

    df = df.fillna(0)
    df["cpu_rec"] = (df["cpu_p95"] * HEADROOM).clip(lower=0.01)
    df["mem_rec"] = df["mem_p95"] * HEADROOM
    df["cpu_waste_pct"] = ((df["cpu_req"] - df["cpu_rec"]) / df["cpu_req"] * 100).clip(lower=0)
    df["mem_waste_pct"] = ((df["mem_req"] - df["mem_rec"]) / df["mem_req"] * 100).clip(lower=0)

    out = pd.DataFrame(
        {
            "pod": df["pod"],
            "cpu_req(cores)": df["cpu_req"].round(2),
            "cpu_rec(cores)": df["cpu_rec"].round(3),
            "cpu_waste%": df["cpu_waste_pct"].round(0),
            "mem_req(MiB)": (df["mem_req"] / 2**20).round(0),
            "mem_rec(MiB)": (df["mem_rec"] / 2**20).round(0),
            "mem_waste%": df["mem_waste_pct"].round(0),
        }
    )
    print(out.to_string(index=False))
    out.to_csv("analysis/report.csv", index=False)
    print("\nSaved: analysis/report.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
