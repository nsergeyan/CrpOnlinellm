import random

from crp.framework.knowledge import SEEDS
from crp.gp.algorithm import _best_index, _select_worst, run_gp
from crp.gp.expression import make_priority
from crp.gp.fitness import CachedFitness, total_relocations
from crp.gp.mutation import mutate
from crp.gp.tree import GPTree, random_tree
from crp.llm.evaluate import compile_rule, total_or_raise
from crp.schemes import solve_unrestricted
from crp.yard import Yard


def size_fitness(text):
    """Fake fitness for fast tests: shorter formulas are better."""
    return len(text.split())


def test_worst_selection_ties_keep_the_first():
    scores = [5, 7, 7, 1]
    assert _select_worst([1, 2, 0], scores) == 1  # 7 and 7: the first stays
    assert _select_worst([0, 3, 2], scores) == 2


def test_best_selection_ties_take_the_last():
    assert _best_index([3, 1, 4, 1]) == 3


def test_budget_is_initial_population_plus_generations():
    result = run_gp(size_fitness, random.Random(0), population_size=20, generations=5)
    assert result.evaluations == 20 + 5 * 20
    assert [h[0] for h in result.history] == [0, 1, 2, 3, 4, 5]


def test_best_never_gets_worse_and_improves():
    result = run_gp(size_fitness, random.Random(1), population_size=50, generations=20)
    best = [h[2] for h in result.history]
    assert best == sorted(best, reverse=True)
    assert best[-1] < best[0]
    assert result.best_fitness == size_fitness(result.best.text())


def test_same_seed_same_run():
    a = run_gp(size_fitness, random.Random(2), population_size=30, generations=5)
    b = run_gp(size_fitness, random.Random(2), population_size=30, generations=5)
    assert a.best == b.best and a.history == b.history


def test_cache_does_not_change_the_run():
    plain = run_gp(size_fitness, random.Random(3), population_size=30, generations=5)
    cached = CachedFitness(size_fitness)
    with_cache = run_gp(cached, random.Random(3), population_size=30, generations=5)
    assert plain.best == with_cache.best and plain.history == with_cache.history
    assert cached.hits > 0  # repeated formulas were not recomputed, but still counted


def test_short_run_on_real_fitness(training_set):
    instances = training_set[::40]  # one yard per class, to keep the test fast
    fitness = CachedFitness(lambda text: total_relocations(text, instances, 0.5))
    result = run_gp(fitness, random.Random(4), population_size=10, generations=2)
    assert result.evaluations == 30
    assert result.best_fitness == total_relocations(result.best.text(), instances, 0.5)


def test_start_formula_is_in_the_first_population():
    result = run_gp(size_fitness, random.Random(5), population_size=20, generations=0, start=("MM",))
    assert result.evaluations == 20
    assert result.best == GPTree(("MM",))  # one node: shorter than any random tree


def test_minmax_formula_is_the_framework_start_rule(training_set):
    instances = training_set[::40]
    start_rule = compile_rule(SEEDS["minmax"][1], "priority")
    for alpha in (0.5, 0.1):
        fast = total_relocations("MM", instances, alpha)
        assert fast == total_or_raise(start_rule, instances, alpha)
        assert fast == sum(solve_unrestricted(Yard(inst, alpha), make_priority("MM")) for inst in instances)


def test_extra_terminal_reaches_random_trees_and_mutations():
    terminals = ("SH", "MM")
    result = run_gp(size_fitness, random.Random(6), population_size=30, generations=3, terminals=terminals)
    assert set(result.best.nodes) <= {"SH", "MM", "+", "-", "*", "/"}
    trees = [random_tree(random.Random(seed), terminals) for seed in range(20)]
    assert any("MM" in tree.nodes for tree in trees)
    assert all(set(tree.nodes) <= {"SH", "MM", "+", "-", "*", "/"} for tree in trees)
    mutated = [mutate(GPTree.from_text("+ SH SH"), random.Random(seed), 1.0, terminals) for seed in range(200)]
    assert any("MM" in tree.nodes for tree in mutated)
