#!/usr/bin/env python

import argparse
import time
import timeit
from pathlib import Path
from random import choice, randint, randrange, seed
from subprocess import TimeoutExpired

import multiprocess as mp
import tadashi
# or
from mpi4py import futures
from mpi4py.futures import MPIPoolExecutor as Executor
from mpi4py.futures import as_completed
from tadashi import TRANSFORMATIONS, LowerUpperBound, Scops, TrEnum
from tadashi.apps import Polybench, Simple


def legalAndTransform(node, tr, args):
    try:
        return node.transform(tr, *args)
    except ValueError:
        print("Still having issues ")
        return False


def isValidNode(scops, op):
    coords, transformation, args = op
    node = scops[coords[0]].schedule_tree[coords[1]]
    valid = legalAndTransform(node, transformation, args)
    node.rollback()
    if not valid:
        return False
    return True


def random_args(node, tr):
    tiles = [TrEnum.TILE1D, TrEnum.TILE2D, TrEnum.TILE3D]
    if tr in tiles:
        tile_size = choice([2**x for x in range(5, 10)])
        return [tile_size] * (1 + tiles.index(tr))
    return choice(node.get_args(tr, start=-64, end=64))


def getFitnessGlobal(
    op_list=None, app_factory=None, n_trials: int = None, timeout=9999
):
    """
    app_factory and n_trials are not requires if the fitness is already calculated
    """
    app = app_factory.generate_code(populate_scops=True)

    app.transform_list(op_list)

    evals = []
    for _ in range(n_trials):
        try:
            evals.append(app.measure(timeout=timeout))
        except TimeoutExpired:
            # If the evaluations takes too long, it gets a bad fitness
            evals.append(timeout)

    # multiplied by -1 so fitness is meant to be maximized
    return -1 * min(evals)


class Individual:
    operation_list: list = None
    fitness: float = None

    def __init__(self, op: list = []):
        self.operation_list = op

    def __str__(self):
        f = "%.8f" % self.fitness if not self.fitness is None else "Not evaluated"
        tmp = "["
        for op in self.operation_list:
            tmp += "[%s, %s, %s], " % (
                str(op[0:2]),
                "tadashi.TrEnum." + op[2].name,
                str(op[3:]),
            )
        tmp += "]"
        return "%s --- %s" % (tmp, f)

    def __gt__(self, other):
        # You must calculate everyones fitness before sorting
        return self.getFitness() > other.getFitness()

    def generateCode(self, app_factory):
        app = app_factory.generate_code(ephemeral=False, populate_scops=True)
        app.transform_list(self.operation_list)
        return app

    def getFitness(self, app_factory=None, n_trials: int = None, timeout=9999):
        """
        app_factory and n_trials are not requires if the fitness is already calculated
        """
        if self.fitness is None:
            app = app_factory.generate_code()

            app.transform_list(self.operation_list)

            evals = []
            for _ in range(n_trials):
                try:
                    evals.append(app.measure(timeout=timeout))
                except TimeoutExpired:
                    # If the evaluations takes too long, it gets a bad fitness
                    evals.append(timeout)

            # multiplied by -1 so fitness is meant to be maximized
            self.fitness = -1 * min(evals)

        return self.fitness

    def isLegal(self, app_factory=None):
        app = app_factory.generate_code(populate_scops=True)
        try:
            return app.transform_list(self.operation_list)
        except ValueError:
            # If the transform_list fails, its not a valid list
            return False

    def crossover(self, other, app_factory=None):
        # 50% chance to crossover, 0% if either parents have length 0
        if (
            randint(0, 9) < 5
            and len(self.operation_list) * len(other.operation_list) > 0
        ):
            p1 = self.operation_list
            p2 = other.operation_list

            xop1 = randint(0, len(p1) - 1)
            xop2 = randint(0, len(p2) - 1)

            o1 = p1[:xop1] + p2[:xop2]
            o2 = p2[:xop2] + p1[:xop1]

            i1 = Individual(o1)
            i2 = Individual(o2)

            ret = []
            for i in [i1, i2]:
                # print(">> XO")
                if i.isLegal(app_factory):
                    ret.append(i)
                # print("<< XO")

            return ret

        else:
            return [self, other]

    def mutate(self, app_factory=None):
        app = app_factory.generate_code(populate_scops=True)
        # 10% not mutate
        # 10% lose last operation or not mutate
        # 80% of appending a new operation at the end
        mutationType = randint(0, 9)

        # No mutation
        if mutationType == 0:
            return self

        # Delete last node, if exists:
        if mutationType == 1:
            op_list = self.operation_list[:-1]
            ret = Individual(op_list)
            return ret if ret.isLegal(app_factory) else None

        if mutationType > 1:

            found = False
            op_list = self.operation_list[:]

            app.transform_list(self.operation_list)

            scops = app.scops

            # print("Mutating 1")
            at = 0
            while not found:
                at += 1
                # print("Trying to find valid mut")
                x1 = randint(0, len(scops) - 1)
                st = scops[x1].schedule_tree
                x2 = randint(0, len(st) - 1)
                node = st[x2]

                possible = node.available_transformations
                if len(possible) > 0:
                    tran = possible[randint(0, len(possible) - 1)]
                    args = random_args(node, tran)

                    op = [x1, x2, tran, *args]

                    tmp_op = op_list[:]
                    tmp_op.append(op)

                    ret = Individual(tmp_op)

                    # print(">>MUT")
                    legal = ret.isLegal(app_factory)
                    # print("<<MUT")

                    found = legal
            # print("Found MUT after %d attempts" % at)

            return ret


class EvolTadashi:
    population = None
    max_gen = None
    best_individual = None
    n_trials = None
    app = None
    t_size = None
    n_threads = None

    def __init__(
        self,
        app_factory,
        population_size=30,
        max_gen=20,
        n_trials=2,
        t_size=2,
        n_threads=1,
        timeout=9999,
    ):
        self.app_factory = app_factory
        # The initial population is an individual without transformations
        # so the algorithm starts by searching for simpler solutions first
        self.population = [Individual()]
        self.population_size = population_size
        self.max_gen = max_gen
        self.n_trials = n_trials
        self.t_size = t_size
        self.n_threads = n_threads
        self.timeout = timeout

    def tournament(self):
        """
        Requires: sorted population
        """
        return self.population[
            min([randint(0, len(self.population) - 1) for _ in range(self.t_size)])
        ]

    def fit(self):

        self.best_individual = self.population[0]
        self.best_individual.getFitness(self.app_factory, self.n_trials)
        print(
            "Measure without transformations:",
            self.best_individual.getFitness(self.app_factory, self.n_trials),
        )

        for gen in range(self.max_gen):
            print("Gen %d" % gen)

            # print("  Calc fitness")
            # [i.getFitness( self.app_factory, self.n_trials, timeout=self.timeout ) for i in self.population]
            # self.population.sort(reverse=True)

            start_time = time.time()
            if self.n_threads > 1:
                execut = False
                if execut:
                    fs = {}
                    with Executor(max_workers=5) as executor:
                        for ind in self.population:
                            future = executor.submit(
                                getFitnessGlobal,
                                ind.generateCode(),
                                self.n_trials,
                                self.timeout,
                            )
                            fs[future] = ind  # Store the mapping

                        for future in as_completed(fs):  # Process completed futures
                            if future.exception():
                                print(f"Future raised an error: {future.exception()}")
                            print(
                                dir(future), future._result, future._Future__get_result
                            )
                            ind = fs[future]  # Retrieve the corresponding individual
                            ind.fitness = (
                                future.result()
                            )  # Assign the fitness value correctly

                        print([ind.fitness for ind in self.population])
                        # assert False
                else:
                    with mp.Pool(processes=self.n_threads) as pool:
                        results = pool.map(
                            multiProcess_fitnessEval,
                            [
                                (
                                    ind.generateCode(self.app_factory),
                                    self.n_trials,
                                    self.timeout,
                                )
                                for ind in self.population
                            ],
                        )
                        for i in range(len(self.population)):
                            self.population[i].fitness = results[i]
            else:
                [
                    i.getFitness(self.app_factory, self.n_trials, timeout=self.timeout)
                    for i in self.population
                ]

            self.population.sort(reverse=True)

            end_time = time.time()
            print("Evaluation time:", end_time - start_time)

            print("  Fitness values obtained:")
            [print("   ", i.fitness, i) for i in self.population]

            if self.population[0] > self.best_individual:
                self.best_individual = self.population[0]
                print("  Updating best_individual to", self.best_individual)

            # print("  Breeding phase")
            new_pop = []
            while len(new_pop) < self.population_size:
                ind1 = self.tournament()
                ind2 = self.tournament()
                # print("	MUT")
                ind1 = ind1.mutate(self.app_factory)
                ind2 = ind2.mutate(self.app_factory)
                # print("	XO")
                ret = ind1.crossover(ind2, self.app_factory)
                new_pop.extend(ret)
            new_pop = new_pop[: self.population_size]

            self.population = new_pop

            print(
                "  Fitness on generation %d: %.8f"
                % (
                    gen,
                    self.best_individual.getFitness(self.app_factory, self.n_trials),
                )
            )

        print("Final model:", self.best_individual)


def multiProcess_fitnessEval(a):
    app, trials, timeout = a

    evals = []
    for _ in range(trials):
        try:
            evals.append(app.measure(timeout=timeout))
        except TimeoutExpired:
            # If the evaluations takes too long, it gets a bad fitness
            evals.append(timeout)

    # multiplied by -1 so fitness is meant to be maximized
    return -1 * min(evals)


def main(args):
    seed(args.seed)
    print(f"Opening {args.benchmark}")
    dataset = f"-D{args.dataset}_DATASET"
    print(f"Using {dataset}")
    app_factory = Polybench(args.benchmark, compiler_options=[dataset])
    app_factory.compile()
    full_runtime = timeit.timeit(app_factory.measure, number=1)
    print("USING TIME LIMIT:", full_runtime)
    m = EvolTadashi(
        app_factory,
        population_size=args.population_size,
        max_gen=args.max_gen,
        n_trials=args.n_trails,
        n_threads=args.n_threads,
        timeout=2 * full_runtime,
    )
    m.fit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=str, default="gemm")
    parser.add_argument("--dataset", type=str, default="EXTRALARGE")
    parser.add_argument("--seed", type=int, default=47)
    parser.add_argument("--population-size", type=int, default=20)
    parser.add_argument("--max-gen", type=int, default=10)
    parser.add_argument("--n-trails", type=int, default=10)
    parser.add_argument("--n-threads", type=int, default=1)
    args = parser.parse_args()
    main(args)
