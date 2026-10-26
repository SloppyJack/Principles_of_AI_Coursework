"""Produce auditable summaries, figures and a Chinese group report from raw runs."""
import csv
import json
import os
from pathlib import Path

import numpy as np

LABELS = {"pc_0.0": "Pc=0.0", "pc_0.2": "Pc=0.2", "pc_0.5": "Pc=0.5",
          "pc_0.8": "Pc=0.8 / baseline", "pc_1.0": "Pc=1.0",
          "select_roulette": "Roulette", "select_rank": "Linear rank",
          "cross_one_point": "One point", "cross_uniform": "Uniform", "mut_adaptive": "Adaptive"}
CHINESE = {"pc_0.0": "Pc=0.0", "pc_0.2": "Pc=0.2", "pc_0.5": "Pc=0.5",
           "pc_0.8": "基准：Pc=0.8", "pc_1.0": "Pc=1.0", "select_roulette": "轮盘赌选择",
           "select_rank": "线性排序选择", "cross_one_point": "单点交叉",
           "cross_uniform": "均匀交叉", "mut_adaptive": "自适应变异"}


def summarize(output):
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/ga-lab-matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    manifest = json.loads((output / "manifest.json").read_text())
    records = [json.loads(line) for line in (output / "runs.jsonl").read_text().splitlines()]
    groups = {config["id"]: [r for r in records if r["config_id"] == config["id"]]
              for config in manifest["configurations"]}
    baseline = groups[manifest["baseline_id"]]
    rows = []
    bootstrap_rng = np.random.default_rng(314159)
    resamples = bootstrap_rng.integers(len(baseline), size=(10000, len(baseline)))
    for key, runs in groups.items():
        assert [r["seed"] for r in runs] == [r["seed"] for r in baseline]
        assert [r["initial_sha256"] for r in runs] == [r["initial_sha256"] for r in baseline]
        final = np.array([r["final_best"] for r in runs])
        hits = np.array([r["penalized_hit"] for r in runs])
        delta = hits - np.array([r["penalized_hit"] for r in baseline])
        low, high = np.quantile(delta[resamples].mean(axis=1), [0.025, 0.975])
        successful = [r["first_hit"] for r in runs if r["success"]]
        row = {"config_id": key, "n": len(runs), "best_mean": float(final.mean()),
               "best_std": float(final.std(ddof=1)), "best_min": int(final.min()), "best_max": int(final.max()),
               "successes": len(successful), "success_rate": len(successful) / len(runs),
               "hit_mean_success_only": float(np.mean(successful)) if successful else None,
               "penalized_hit_mean": float(hits.mean()), "penalized_hit_std": float(hits.std(ddof=1)),
               "paired_delta_mean": float(delta.mean()), "paired_delta_ci_low": float(low),
               "paired_delta_ci_high": float(high), "seconds_mean": float(np.mean([r["elapsed_seconds"] for r in runs]))}
        rows.append(row)
    with (output / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (output / "summary.json").write_text(json.dumps(rows, indent=2))
    figures = output / "figures"
    figures.mkdir(exist_ok=True)
    panels = [("Crossover probability", [f"pc_{p:.1f}" for p in (0, .2, .5, .8, 1)]),
              ("Selection operator", ["pc_0.8", "select_roulette", "select_rank"]),
              ("Crossover operator", ["pc_0.8", "cross_one_point", "cross_uniform"]),
              ("Mutation operator", ["pc_0.8", "mut_adaptive"])]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    for ax, (title, keys) in zip(axes.flat, panels):
        for key in keys:
            curves = np.array([[h["best"] for h in r["history"]] for r in groups[key]])
            mean, sd = curves.mean(axis=0), curves.std(axis=0, ddof=1)
            ax.plot(mean, label=LABELS[key])
            ax.fill_between(range(len(mean)), mean - sd, np.minimum(100, mean + sd), alpha=.12)
        ax.set(title=title, xlabel="Generation", ylabel="Best fitness (mean +/- SD)", ylim=(55, 101))
        ax.legend(fontsize=8); ax.grid(alpha=.2)
    fig.savefig(figures / "convergence.png", dpi=180); plt.close(fig)
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), constrained_layout=True)
    names = [LABELS[r["config_id"]] for r in rows]
    colors = ["#3567aa" if r["config_id"] != "pc_0.8" else "#d67526" for r in rows]
    axes[0].bar(names, [r["success_rate"] * 100 for r in rows], color=colors)
    axes[0].set(ylabel="Success rate (%)", ylim=(0, 110), title=f"Fixed budget; {len(baseline)} paired seeds")
    axes[1].bar(names, [r["penalized_hit_mean"] for r in rows],
                yerr=[r["penalized_hit_std"] for r in rows], capsize=3, color=colors)
    axes[1].set(ylabel="Penalized hitting generation", title="Failure assigned G+1; lower is better; error bars = SD")
    for ax in axes:
        ax.tick_params(axis="x", rotation=30); ax.grid(axis="y", alpha=.2)
    fig.savefig(figures / "performance.png", dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
    for key in ("pc_0.8", "mut_adaptive"):
        for ax, metric in zip(axes, ("diversity", "pm")):
            curves = np.array([[h[metric] for h in r["history"]] for r in groups[key]])
            ax.plot(curves.mean(axis=0), label=LABELS[key])
    axes[0].set(xlabel="Generation", ylabel="Normalized gene diversity")
    axes[1].set(xlabel="Generation", ylabel="Per-bit mutation probability (next step)")
    for ax in axes: ax.legend(); ax.grid(alpha=.2)
    fig.savefig(figures / "mutation_dynamics.png", dpi=180); plt.close(fig)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    summarize(parser.parse_args().results)
