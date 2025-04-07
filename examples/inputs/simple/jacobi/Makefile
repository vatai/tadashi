
CC = gcc
CFLAGS = -Wall -Wextra -O3 # Add your desired CFLAGS here

TARGETS = base tiled

SRCS = $(addsuffix .c, $(TARGETS))

%: %.c
	$(CC) $(CFLAGS) -o $@ $<

all: $(TARGETS)

clean:
	rm -f $(TARGETS)