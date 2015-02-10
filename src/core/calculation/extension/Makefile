CFLAGS=-O3 -I/usr/local/gr/include
LDFLAGS=-L/usr/local/gr/lib -lGR3
SUBDIRS=


all: libalgorithm.so subdirs

libalgorithm.so: algorithm.c
	$(CC) -Wall -Wextra -fPIC ${CFLAGS} -o $@ $< -shared $(LDFLAGS)

subdirs:
	for i in $(SUBDIRS); do make -C $$i all; done

clean:
	rm -f *.pyc *.pyo
	rm -f *.o *.so
	for i in $(SUBDIRS); do make -C $$i clean; done

