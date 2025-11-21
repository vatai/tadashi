# distutils: language=c++
import cython
from cython.cimports import pet


@cython.cclass
class Scop:
    _scop = cython.declare(pet.pet_scop_p)

    def __cinit__(self, scop: pet.pet_scop_p):
        self._scop = scop

    def __dealloc__(self):
        if self._scop is not cython.NULL:
            pet.pet_scop_free(self._scop)
