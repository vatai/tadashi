#!/usr/bin/env python

import time
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


def get_polybench_list():
    base = Path("examples/polybench")
    result = []
    for p in base.glob("**"):
        if Path(p / (p.name + ".c")).exists():
            result.append(p.relative_to(base))
    return base, result


def random_args(node, tr):
    if tr == TrEnum.TILE1D:
        tile_size = choice([2**x for x in range(5, 12)])
        return [tile_size]
    return choice(node.get_args(tr, start=-64, end=64))


def getFitnessGlobal(
    op_list=None, app_factory=None, n_trials: int = None, timeout=9999
):
    """
    app_factory and n_trials are not requires if the fitness is already calculated
    """
    app = app_factory.generate_code()

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
        app = app_factory.generate_code(ephemeral=False)
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
        app = app_factory.generate_code()
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
        app = app_factory.generate_code()
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


# Baseline
if False:
    measures = {}
    base, poly = get_polybench_list()
    for i, p in list(enumerate(poly)):
        app_factory = Polybench(p, base, compiler_options=["-DLARGE_DATASET"])
        app_factory.compile()
        measures[p.name] = min([app_factory.measure() for _ in range(10)])

    print(measures)
else:
    measures100_medium = {
        "floyd-warshall": 0.231437,
        "nussinov": 0.045746,
        "deriche": 0.009837,
        "syr2k": 0.025297,
        "gesummv": 0.00021,
        "gemver": 0.001175,
        "trmm": 0.012824,
        "symm": 0.019753,
        "syrk": 0.017595,
        "gemm": 0.023244,
        "atax": 0.00062,
        "bicg": 0.000505,
        "2mm": 0.033326,
        "doitgen": 0.01744,
        "3mm": 0.051028,
        "mvt": 0.000784,
        "lu": 0.062938,
        "durbin": 0.000385,
        "ludcmp": 0.04525,
        "cholesky": 0.031638,
        "trisolv": 0.000196,
        "gramschmidt": 0.029388,
        "heat-3d": 0.130359,
        "jacobi-1d": 0.000148,
        "fdtd-2d": 0.044368,
        "adi": 0.0823,
        "jacobi-2d": 0.03749,
        "seidel-2d": 0.134414,
        "covariance": 0.019191,
        "correlation": 0.018919,
    }

    measures10_large = {
        "floyd-warshall": 41.125441,
        "nussinov": 8.509897,
        "deriche": 0.272917,
        "syr2k": 3.51393,
        "gesummv": 0.005931,
        "gemver": 0.032582,
        "trmm": 1.715369,
        "symm": 2.918881,
        "syrk": 1.895187,
        "gemm": 2.890105,
        "atax": 0.015809,
        "bicg": 0.012656,
        "2mm": 4.587687,
        "doitgen": 1.263066,
        "3mm": 7.045617,
        "mvt": 0.021109,
        "lu": 7.279469,
        "durbin": 0.009948,
        "ludcmp": 6.30028,
        "cholesky": 2.948051,
        "trisolv": 0.00464,
        "gramschmidt": 4.102933,
        "heat-3d": 14.484053,
        "jacobi-1d": 0.004999,
        "fdtd-2d": 4.233523,
        "adi": 10.925085,
        "jacobi-2d": 5.138872,
        "seidel-2d": 16.90997,
        "covariance": 3.477201,
        "correlation": 3.461664,
    }


if __name__ == "__main__":

    seed(47)
    simple = False

    if simple:
        app_factory = Simple("examples/depnodep.c")
    else:
        base, poly = get_polybench_list()
        print(poly)
        for i, p in list(enumerate(poly))[8:9]:
            print("Opening %s" % p.name)
            print(p, base)
            # app_factory = Polybench(p, base, compiler_options=["-DSMALL_DATASET"])
            app_factory = Polybench(p, base, compiler_options=["-DLARGE_DATASET"])
            # app = Polybench(p, base, compiler_options=["-DMEDIUM_DATASET"])
            break

    print("USING TIME LIMIT:", measures10_large[p.name] * 5)
    m = EvolTadashi(
        app_factory,
        population_size=20,
        max_gen=10,
        n_trials=10,
        n_threads=3,
        timeout=measures10_large[p.name] * 5,
    )
    m.fit()


# PosixPath('medley/floyd-warshall'),
# PosixPath('medley/nussinov'),
# PosixPath('medley/deriche'),
# PosixPath('linear-algebra/blas/syr2k'),
# PosixPath('linear-algebra/blas/gesummv'),
# PosixPath('linear-algebra/blas/gemver'),
# PosixPath('linear-algebra/blas/trmm'),
# PosixPath('linear-algebra/blas/symm'),
# PosixPath('linear-algebra/blas/syrk'),
# PosixPath('linear-algebra/blas/gemm'),
# PosixPath('linear-algebra/kernels/atax'),
# PosixPath('linear-algebra/kernels/bicg'),
# PosixPath('linear-algebra/kernels/2mm'),
# PosixPath('linear-algebra/kernels/doitgen'),
# PosixPath('linear-algebra/kernels/3mm'),
# PosixPath('linear-algebra/kernels/mvt'),
# PosixPath('linear-algebra/solvers/lu'),
# PosixPath('linear-algebra/solvers/durbin'),
# PosixPath('linear-algebra/solvers/ludcmp'),
# PosixPath('linear-algebra/solvers/cholesky'),
# PosixPath('linear-algebra/solvers/trisolv'),
# PosixPath('linear-algebra/solvers/gramschmidt'),
# PosixPath('stencils/heat-3d'),
# PosixPath('stencils/jacobi-1d'),
# PosixPath('stencils/fdtd-2d'),
# PosixPath('stencils/adi'),
# PosixPath('stencils/jacobi-2d'),
# PosixPath('stencils/seidel-2d'),
# PosixPath('datamining/covariance'),
# PosixPath('datamining/correlation')
