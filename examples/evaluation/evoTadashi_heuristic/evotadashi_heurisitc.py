
import argparse
import time
import timeit
from pathlib import Path
from random import choice, randint, randrange, seed
from subprocess import TimeoutExpired

import multiprocess as mp
import tadashi
from tadashi import TRANSFORMATIONS, LowerUpperBound, Scops, TrEnum
from tadashi.apps import Polybench, Simple

####
####
def getDepth_aux(node, depth=0):
    cl = node.children
    if len(cl) == 0:
        return depth
    else:
        return max( [getDepth_aux(c, depth+1) for c in cl] )

def getDepth(app, node_id):
    base_node = app.scops[0].schedule_tree[node_id]
    return getDepth_aux(base_node)


def searchFor(app, tr_name):
    scops = app.scops
    ret = []
    for si in range(len(scops[0].schedule_tree)):
        s = scops[0].schedule_tree[si]
        av = s.available_transformations
        for t in av:
            if t == tr_name:
                ret.append(si)
    return ret
####
####

def random_args(node, tr):
    tiles = [TrEnum.TILE1D, TrEnum.TILE2D, TrEnum.TILE3D]
    if tr in tiles:
        tile_size = choice([2**x for x in range(5, 10)])
        return [tile_size] * (1 + tiles.index(tr))
    if tr in [TrEnum.SET_PARALLEL]:
        return [0]
    return choice(node.get_args(tr, start=-64, end=64))


def multiProcess_fitnessEval(a):
    app, trials, timeout, pre_evaluated = a

    if pre_evaluated != 0:
        return pre_evaluated

    evals = []
    for _ in range(trials):
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
        """
        You must calculate everyones fitness before sorting
        """
        return self.getFitness() > other.getFitness()

    def generateCode(self, app_factory):
        app = app_factory.generate_code(populate_scops=True)
        app.transform_list(self.operation_list)
        tapp = app.generate_code()
        tapp.compile()
        return tapp

    def getFitness(
        self, app_factory=None, n_trials: int = None, timeout=9999, evaluations=None
    ):
        """
        app_factory and n_trials are not requires if the fitness is already calculated
        """
        if not evaluations is None and str(self.operation_list) in evaluations:
            self.fitness = evaluations[str(self.operation_list)]

        if self.fitness is None:
            try:
                app = self.generateCode(app_factory)
                evals = []
                for _ in range(n_trials):
                    try:
                        evals.append(app.measure(timeout=timeout))
                    except TimeoutExpired:
                        # If the evaluations takes too long, it gets a bad fitness
                        evals.append(timeout)
            except CalledProcessError:
                print(str(self))
                assert False

            # multiplied by -1 so fitness is meant to be maximized
            self.fitness = -1 * min(evals)

        if not evaluations is None:
            evaluations[str(self.operation_list)] = self.fitness
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
                #possible = [p for p in possible if p[1]!=TrEnum.SET_PARALLEL]
                possible = [p for p in possible if not ("TrEnum.SET_PARALLEL" in str(p[1]) or "SHIFT" in str(p[1])) ]

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
    evaluations = None

    def __init__(
        self,
        app_factory,
        population_size=30,
        max_gen=20,
        n_trials=2,
        t_size=2,
        n_threads=1,
        timeout=9999,
        use_heuristic = False,
    ):
        self.app_factory = app_factory
        self.use_heuristic = use_heuristic
        # The initial population is an individual without transformations
        # so the algorithm starts by searching for simpler solutions first

        ########
        ########
        ########

        app = self.app_factory

        full_tr_list = []

        tile_size = 32

        scops = app.scops


        trs = searchFor(app, "full_split")
        trs = [[index, TrEnum.FULL_SPLIT] for index in trs]
        trs = trs[::-1]
        for t in trs:
            scops[0].reset()
            scops[0].transform_list(full_tr_list)
            valid = scops[0].transform_list([t])
            if valid[-1]:
                full_tr_list.append(t)
        scops[0].reset()
        valid = scops[0].transform_list(full_tr_list)

        trs = searchFor(app, "tile3d")
        toRemoveFrom2D = [a for a in trs]
        toRemoveFrom2D.extend([a + 1 for a in trs])
        toRemoveFrom2D = list(set(toRemoveFrom2D))
        for t in trs:
            if t - 1 in trs:
                trs.pop(trs.index(t - 1))
        trs3D = [
            [index, TrEnum.TILE3D, tile_size, tile_size, tile_size] for index in trs[::-1]
        ]


        trs2 = searchFor(app, "tile2d")
        trs2D = [[index, TrEnum.TILE2D, tile_size, tile_size] for index in trs2[::-1]]
        trs3D.extend(trs2D)
        trs3D.sort()
        trs3D = trs3D[::-1]
        for t in trs3D:
            scops[0].reset()
            scops[0].transform_list(full_tr_list)
            valid = scops[0].transform_list([t])
            if valid[-1]:
                full_tr_list.append(t)
        scops[0].reset()

        ########
        ########
        ########


        self.population = [Individual()]

        #####
        #####

        if self.use_heuristic:
            full_tr_list = [ [0]+t for t in full_tr_list]
        else:
            full_tr_list = []
        print(full_tr_list)

        for i in range(1,len(full_tr_list)):
            ind = Individual(op=full_tr_list[:1])
            legal = ind.isLegal(self.app_factory)
            if legal:
                self.population.append( Individual(op=full_tr_list[:i]) )
            else:
                print("sus")

        #####
        #####

        self.population_size = population_size
        self.max_gen = max_gen
        self.n_trials = n_trials
        self.t_size = t_size
        self.n_threads = n_threads
        self.timeout = timeout
        self.evaluations = {}

    def tournament(self):
        """
        Requires: sorted population
        """
        return self.population[
            min([randint(0, len(self.population) - 1) for _ in range(self.t_size)])
        ]

    def fit(self):

        self.best_individual = self.population[0]
        self.best_individual.getFitness(
            self.app_factory, self.n_trials, evaluations=self.evaluations
        )
        print(
            "Measure without transformations:",
            self.best_individual.getFitness(
                self.app_factory, self.n_trials, evaluations=self.evaluations
            ),
        )

        for gen in range(self.max_gen):
            print("Gen %d" % gen)

            # print("  Calc fitness")
            # [i.getFitness( self.app_factory, self.n_trials, timeout=self.timeout ) for i in self.population]
            # self.population.sort(reverse=True)

            start_time = time.time()
            if self.n_threads > 1:
                with mp.Pool(processes=self.n_threads) as pool:
                    results = pool.map(
                        multiProcess_fitnessEval,
                        [
                            (
                                ind.generateCode(self.app_factory),
                                self.n_trials,
                                self.timeout,
                                (
                                    self.evaluations[str(ind.operation_list)]
                                    if str(ind.operation_list) in self.evaluations
                                    else 0
                                ),
                            )
                            for ind in self.population
                        ],
                    )
                    for i in range(len(self.population)):
                        self.population[i].fitness = results[i]
                        self.evaluations[str(self.population[i].operation_list)] = (
                            results[i]
                        )
            else:
                [
                    i.getFitness(
                        self.app_factory,
                        self.n_trials,
                        timeout=self.timeout,
                        evaluations=self.evaluations,
                    )
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
                "  Fitness on generation %d: %.8f (%.3fx speedup)"
                % (
                    gen,
                    self.best_individual.getFitness(self.app_factory, self.n_trials),
                    self.evaluations["[]"]/self.best_individual.getFitness(self.app_factory, self.n_trials)
                )
            )

        print("Final model:", self.best_individual)

        ########
        ########

        full_tr_list = [t[1:] for t in  self.best_individual.operation_list]

        app = self.app_factory
        scops = app.scops
        valid = scops[0].transform_list(full_tr_list)

        trs = searchFor(app, "set_parallel")
        trs = [[index, TrEnum.SET_PARALLEL, 0] for index in trs]

        trs = trs[::-1]
        tmp = []
        for t in trs:
            tmp.append( [getDepth(app, t[0]), t] )
        tmp.sort()
        trs = [tmp[-1][1]]

        for t in trs:
            scops[0].reset()
            scops[0].transform_list(full_tr_list)
            valid = scops[0].transform_list([t])
            if valid[-1]:
                full_tr_list.append(t)
        scops[0].reset()
        valid = scops[0].transform_list(full_tr_list)

        tiled = app.generate_code(alt_infix="_tiled", ephemeral=True)
        tiled.compile()

        improved = tiled.measure()
        print("Time with parallel: %f (%.3fx speedup)" % (improved, self.evaluations["[]"]/improved))


        print("FINAL transformation_list=[")
        [print("   %s," % str(t)) for t in full_tr_list]
        print("]")

        ########
        ########


def main(args):
    seed(args.seed)
    print(f"Opening {args.benchmark}")
    dataset = f"-D{args.dataset}_DATASET"
    oflag = f"-O{args.oflag}"
    print(f"Using {dataset}")
    app_factory = Polybench(args.benchmark, compiler_options=[dataset, oflag])
    app_factory.compile()
    timeout = timeit.timeit(app_factory.measure, number=1) * 2
    print("USING TIME LIMIT:", timeout)
    m = EvolTadashi(
        app_factory,
        population_size=args.population_size,
        max_gen=args.max_gen,
        n_trials=args.n_trails,
        n_threads=args.n_threads,
        use_heuristic = args.use_heuristic,
        timeout=timeout,
    )
    m.fit()


if __name__ == "__main__":
    for benchmark in ["gemm"]: #Polybench.get_benchmarks():
        print("\n\n\n")
        parser = argparse.ArgumentParser()
        parser.add_argument("--benchmark", type=str, default=benchmark)
        parser.add_argument("--dataset", type=str, default="EXTRALARGE")
        parser.add_argument("--oflag", type=int, default=3)
        parser.add_argument("--seed", type=int, default=47)
        parser.add_argument("--population-size", type=int, default=100)
        parser.add_argument("--max-gen", type=int, default=50)
        parser.add_argument("--n-trails", type=int, default=5)
        parser.add_argument("--n-threads", type=int, default=10)
        parser.add_argument("--use-heuristic", action=argparse.BooleanOptionalAction)
        #print(str(parser))
        args = parser.parse_args()
        print(str(args) + "\n")
        main(args)
