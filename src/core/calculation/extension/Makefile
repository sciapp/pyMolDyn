CFLAGS=-O3 
LDFLAGS=
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

