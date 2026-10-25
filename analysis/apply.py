#!/usr/bin/env python3
"""Apply CostPilot's right-sizing recommendations to a Deployment.

Reads analysis/report.csv (produced by `make analyze`), takes the largest
recommended CPU/memory across the pods, rounds it up to friendly values and
patches the Deployment's resource requests/limits with `kubectl set resources`.

Usage:
    python3 analysis/apply.py --namespace demo --deployment demo-app --container app
    python3 analysis/apply.py --dry-run     # only print the command
"""
import argparse
import math
import subprocess
import sys

import pandas as pd

MIN_CPU_M = 50      # never request less than 50m CPU
MIN_MEM_MI = 64     # never request less than 64 MiB memory
CPU_STEP_M = 10     # round CPU up to the next 10m
MEM_STEP_MI = 16    # round memory up to the next 16 MiB


def round_up(value: float, step: int) -> int:
    return int(math.ceil(value / step) * step)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report", default="analysis/report.csv")
    p.add_argument("--namespace", default="demo")
    p.add_argument("--deployment", default="demo-app")
    p.add_argument("--container", default="app")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    try:
        df = pd.read_csv(args.report)
    except FileNotFoundError:
        print(f"{args.report} not found. Run `make analyze` first (needs `make prometheus`).")
        return 1

    if df.empty:
        print("The report is empty. Run the load test first, then `make analyze`.")
        return 1

    cpu_rec_cores = float(df["cpu_rec(cores)"].max())
    mem_rec_mib = float(df["mem_rec(MiB)"].max())

    cpu_req_m = max(MIN_CPU_M, round_up(cpu_rec_cores * 1000, CPU_STEP_M))
    mem_req_mi = max(MIN_MEM_MI, round_up(mem_rec_mib, MEM_STEP_MI))

    # Limits give headroom for spikes: CPU 4x request (min 250m), memory 2x request (min 128Mi).
    cpu_lim_m = max(250, cpu_req_m * 4)
    mem_lim_mi = max(128, mem_req_mi * 2)

    cmd = [
        "kubectl", "-n", args.namespace, "set", "resources",
        f"deployment/{args.deployment}", "-c", args.container,
        f"--requests=cpu={cpu_req_m}m,memory={mem_req_mi}Mi",
        f"--limits=cpu={cpu_lim_m}m,memory={mem_lim_mi}Mi",
    ]

    print(f"Recommended from report : cpu={cpu_rec_cores:.3f} cores, memory={mem_rec_mib:.0f} MiB")
    print(f"Applying requests       : cpu={cpu_req_m}m, memory={mem_req_mi}Mi")
    print(f"Applying limits         : cpu={cpu_lim_m}m, memory={mem_lim_mi}Mi")
    print("Command:", " ".join(cmd))

    if args.dry_run:
        print("Dry run: nothing applied.")
        return 0

    subprocess.run(cmd, check=True)
    subprocess.run(
        ["kubectl", "-n", args.namespace, "rollout", "status",
         f"deployment/{args.deployment}", "--timeout=180s"],
        check=True,
    )
    print("Done. Now run `make load-after`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
