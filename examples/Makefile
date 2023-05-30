CFLAGS=-O2 -g
all: hello1.da hello2.da

%.da: %.o
	objdump -D $< > $@
