FC      = gfortran
FFLAGS  = -O2

FFLAGS_KERNEL = $(FFLAGS)

.PHONY: all clean

all: driver

driver: driver.o kernel.o
	$(FC) $(FFLAGS) -o $@ $^

driver.o: driver.f90
	$(FC) $(FFLAGS) -c -o $@ $<

kernel.o: kernel.f90
	$(FC) $(FFLAGS_KERNEL) -c -o $@ $<

test1:
	./driver --exchange --rhf
test2:
	./driver --coulomb --rhf
test3:
	./driver --exchange --uhf
test4:
	./driver --coulomb --uhf
clean:
	rm -f *.o *.mod driver

