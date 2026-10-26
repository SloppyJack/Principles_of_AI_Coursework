"""Controlled OneMax GA implementation; operator definitions follow DEAP examples.

The upstream source is retained in vendor/. This NumPy implementation is original
and intentionally evaluates the whole population each generation for equal budgets.
"""
from dataclasses import asdict, dataclass
from time import perf_counter

import numpy as np


@dataclass(frozen=True)
class Config:
    length: int = 100
    population: int = 80
    generations: int = 100
    pc: float = 0.8
    selection: str = "tournament"
    crossover: str = "two_point"
    mutation: str = "basic"
    tournament_size: int = 3
    rank_pressure: float = 1.7
    elitism: int = 1

    def validate(self):
        if self.length < 3 or self.population < 4 or self.population % 2:
            raise ValueError("length >= 3; population >= 4 and even")
        if self.generations < 1 or not 0 <= self.pc <= 1:
            raise ValueError("generations >= 1 and pc in [0,1]")
        if self.selection not in {"roulette", "tournament", "rank"}:
            raise ValueError("unknown selection")
        if self.crossover not in {"one_point", "two_point", "uniform"}:
            raise ValueError("unknown crossover")
        if self.mutation not in {"basic", "adaptive"}:
            raise ValueError("unknown mutation")
        if self.tournament_size < 2 or not 1 <= self.rank_pressure <= 2:
            raise ValueError("tournament_size >= 2; rank_pressure in [1,2]")
        if not 0 <= self.elitism < self.population:
            raise ValueError("elitism in [0,population)")


def select_indices(fitness, config, rng):
    n = len(fitness)
    if config.selection == "tournament":
        candidates = rng.integers(n, size=(n, config.tournament_size))
        return candidates[np.arange(n), fitness[candidates].argmax(axis=1)]
    if config.selection == "roulette":
        probabilities = fitness / fitness.sum() if fitness.sum() else np.full(n, 1 / n)
    else:
        # Equal fitness receives the same mean rank, avoiding arbitrary tie bias.
        _, inverse, counts = np.unique(fitness, return_inverse=True, return_counts=True)
        rank = (np.cumsum(counts) - (counts - 1) / 2)[inverse]
        s = config.rank_pressure
        probabilities = (2 - s) / n + 2 * (rank - 1) * (s - 1) / (n * (n - 1))
        probabilities /= probabilities.sum()
    return rng.choice(n, size=n, replace=True, p=probabilities)


def crossover(parents, kind, pc, rng):
    children = parents.copy()
    pairs, length = len(parents) // 2, parents.shape[1]
    apply = rng.random(pairs) < pc
    loci = np.arange(length)[None, :]
    if kind == "one_point":
        cuts = rng.integers(1, length, size=(pairs, 1))
        mask = loci >= cuts
    elif kind == "two_point":
        a = rng.integers(1, length, size=(pairs, 1))
        b = rng.integers(1, length - 1, size=(pairs, 1))
        b += b >= a
        mask = (loci >= np.minimum(a, b)) & (loci < np.maximum(a, b))
    elif kind == "uniform":
        mask = rng.random((pairs, length)) < 0.5
    else:
        raise ValueError(kind)
    mask &= apply[:, None]
    left, right = parents[::2], parents[1::2]
    children[::2] = np.where(mask, right, left)
    children[1::2] = np.where(mask, left, right)
    return children


def diversity(population):
    frequency = population.mean(axis=0)
    return float(np.mean(4 * frequency * (1 - frequency)))


def mutation_probability(config, current_diversity):
    base = 1 / config.length
    return base if config.mutation == "basic" else base + (3 / config.length - base) * (1 - current_diversity)


def run(config=Config(), seed=0):
    config.validate()
    start = perf_counter()
    init_rng, select_rng, cross_rng, mutate_rng = [np.random.default_rng(s)
        for s in np.random.SeedSequence(seed).spawn(4)]
    population = init_rng.integers(0, 2, (config.population, config.length), dtype=np.uint8)
    initial_population = population.copy()
    fitness = population.sum(axis=1)
    first_hit = 0 if fitness.max() == config.length else None
    history = []
    for generation in range(config.generations + 1):
        d = diversity(population)
        pm = mutation_probability(config, d)
        history.append({"generation": generation, "best": int(fitness.max()),
                        "mean": float(fitness.mean()), "diversity": d, "pm": pm})
        if generation == config.generations:
            break
        elites = population[np.argsort(fitness, kind="stable")[-config.elitism:]].copy() if config.elitism else None
        parents = population[select_indices(fitness, config, select_rng)]
        children = crossover(parents, config.crossover, config.pc, cross_rng)
        children ^= (mutate_rng.random(children.shape) < pm).astype(np.uint8)
        # Elites survive unchanged; evaluate a full N-member new population.
        if config.elitism:
            children[:config.elitism] = elites
        population = children
        fitness = population.sum(axis=1)
        if first_hit is None and fitness.max() == config.length:
            first_hit = generation + 1
    best = population[fitness.argmax()]
    assert int(best.sum()) == int(fitness.max())
    assert np.isin(best, [0, 1]).all()
    return {"config": asdict(config), "seed": seed, "initial_population": initial_population.tolist(),
            "best_genome": "".join(map(str, best.tolist())), "final_best": int(fitness.max()),
            "final_mean": float(fitness.mean()), "success": first_hit is not None,
            "first_hit": first_hit, "penalized_hit": first_hit if first_hit is not None else config.generations + 1,
            "evaluations": config.population * (config.generations + 1),
            "elapsed_seconds": perf_counter() - start, "history": history}
