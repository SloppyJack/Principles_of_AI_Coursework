import unittest
from dataclasses import replace
import numpy as np
from ga import Config, crossover, diversity, mutation_probability, run, select_indices


class GeneticAlgorithmTests(unittest.TestCase):
    def test_crossover_preserves_alleles_and_parents(self):
        parents = np.array([[0]*20,[1]*20]*10,dtype=np.uint8)
        original = parents.copy()
        for kind in ('one_point','two_point','uniform'):
            off = crossover(parents,kind,1,np.random.default_rng(0))
            np.testing.assert_array_equal(off[::2]+off[1::2],parents[::2]+parents[1::2])
            self.assertTrue(np.isin(off,[0,1]).all())
            np.testing.assert_array_equal(parents,original)
            np.testing.assert_array_equal(crossover(parents,kind,0,np.random.default_rng(0)),parents)

    def test_run_reproducibility_budget_and_elitism(self):
        config=Config(generations=30,population=20,length=20)
        for mutation in ('basic','adaptive'):
            c=replace(config,mutation=mutation)
            a,b=run(c,123),run(c,123)
            a.pop('elapsed_seconds'); b.pop('elapsed_seconds')
            self.assertEqual(a,b)
            self.assertEqual(a['evaluations'],20*31)
            self.assertEqual(a['final_best'],a['best_genome'].count('1'))
            best=[h['best'] for h in a['history']]
            self.assertTrue(all(y>=x for x,y in zip(best,best[1:])))

    def test_selection_edge_cases(self):
        fitness=np.zeros(80)
        for kind in ('roulette','rank','tournament'):
            ids=select_indices(fitness,replace(Config(),selection=kind),np.random.default_rng(5))
            self.assertEqual(ids.shape,(80,))
            self.assertTrue(((ids>=0)&(ids<80)).all())
        f=np.array([0,0,0,10])
        ids=select_indices(f,replace(Config(population=4),selection='roulette'),np.random.default_rng(0))
        self.assertTrue((ids==3).all())

    def test_adaptation_bounds(self):
        c=replace(Config(),mutation='adaptive')
        self.assertAlmostEqual(diversity(np.array([[0,0],[1,1]])),1)
        self.assertAlmostEqual(diversity(np.ones((4,5))),0)
        self.assertAlmostEqual(mutation_probability(c,1),.01)
        self.assertAlmostEqual(mutation_probability(c,0),.03)

    def test_configs_and_shared_initial_population(self):
        base=run(Config(generations=1),99)
        for c in (replace(Config(),pc=0,generations=1),replace(Config(),selection='rank',generations=1)):
            self.assertEqual(base['initial_population'],run(c,99)['initial_population'])
        for c in (Config(pc=2),Config(population=5),Config(selection='bad')):
            with self.assertRaises(ValueError): run(c)


if __name__=='__main__': unittest.main()
