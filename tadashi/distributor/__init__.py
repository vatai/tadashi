# distributor init

from mpi4py import MPI

RANK = MPI.COMM_WORLD.get_rank()


def master():
    pass


def worker():
    pass


if RANK == 0:
    master()
else:
    worker()
