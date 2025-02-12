# distributor init

from mpi4py import MPI

RANK = MPI.COMM_WORLD.Get_rank()


def master():
    print("I'm the master")
    MPI.COMM_WORLD


def worker():
    print("I'm a worker")
    exit()


def send(lst: list):
    pass


if RANK == 0:
    master()
else:
    worker()
