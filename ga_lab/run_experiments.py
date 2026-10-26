"""Run the archived official example, then paired, controlled operator experiments."""
import argparse
from contextlib import redirect_stdout
from dataclasses import asdict, replace
from datetime import datetime
import csv
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform
import sys

from ga import Config, run

ROOT = Path(__file__).resolve().parent


def configurations():
    base = Config()
    items = [(f"pc_{pc:.1f}", "pc", replace(base, pc=pc)) for pc in (0.0, 0.2, 0.5, 0.8, 1.0)]
    items += [("select_" + s, "selection", replace(base, selection=s)) for s in ("roulette", "rank")]
    items += [("cross_" + c, "crossover", replace(base, crossover=c)) for c in ("one_point", "uniform")]
    items += [("mut_adaptive", "mutation", replace(base, mutation="adaptive"))]
    return items


def official_example(output):
    spec = importlib.util.spec_from_file_location("official_onemax", ROOT / "vendor/onemax_short.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with (output / "original_stdout.txt").open("w") as stream, redirect_stdout(stream):
        pop, log, hof = module.main()
    result = {"best_fitness": float(hof[0].fitness.values[0]), "best_genome": list(hof[0]),
              "history": list(log), "seed": 64, "population": 300, "generations": 40,
              "pc": 0.5, "individual_mutation_probability": 0.2, "bit_flip_probability": 0.05,
              "selection": "tournament3", "crossover": "two_point"}
    (output / "original_result.json").write_text(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--repeats", type=int, default=30)
    parser.add_argument("--first-seed", type=int, default=20261023)
    args = parser.parse_args()
    if args.repeats < 2:
        parser.error("repeats >= 2")
    args.output.mkdir(parents=True, exist_ok=False)
    official_example(args.output)
    seeds = list(range(args.first_seed, args.first_seed + args.repeats))
    manifest = {"created_at": datetime.now().astimezone().isoformat(), "python": sys.version,
                "platform": platform.platform(), "processor": platform.processor(),
                "packages": {name: importlib.metadata.version(name) for name in ("numpy", "matplotlib", "deap")},
                "seeds": seeds, "baseline_id": "pc_0.8", "fixed_generations": True,
                "configurations": [{"id": key, "factor": factor, **asdict(config)}
                                   for key, factor, config in configurations()]}
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    columns = ["config_id", "factor", "seed", "final_best", "final_mean", "success", "first_hit",
               "penalized_hit", "evaluations", "elapsed_seconds", "initial_sha256", "best_genome"]
    initial_hashes = {}
    with (args.output / "runs.jsonl").open("w") as raw, (args.output / "runs.csv").open("w", newline="") as table:
        writer = csv.DictWriter(table, fieldnames=columns)
        writer.writeheader()
        for key, factor, config in configurations():
            for seed in seeds:
                result = run(config, seed)
                initial = json.dumps(result.pop("initial_population"), separators=(",", ":"))
                digest = hashlib.sha256(initial.encode()).hexdigest()
                if seed in initial_hashes:
                    assert digest == initial_hashes[seed]
                else:
                    initial_hashes[seed] = digest
                    (args.output / f"initial_seed_{seed}.json").write_text(initial)
                result.update(config_id=key, factor=factor, initial_sha256=digest)
                raw.write(json.dumps(result) + "\n")
                writer.writerow({name: result.get(name) for name in columns})
            raw.flush()
            print(f"completed {key}: {len(seeds)} runs", flush=True)


if __name__ == "__main__":
    main()
