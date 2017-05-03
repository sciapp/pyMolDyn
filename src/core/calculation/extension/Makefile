CFLAGS = -O3
INCLUDES := $(shell ./build-flags --include-flags gr)
ifeq ($(PYLIBPATH),)
	LDFLAGS := $(shell ./build-flags --lib-flags gr) $(EXTRA_LD_FLAGS)
else
	LDFLAGS := -L$(PYLIBPATH)/python2.7/site-packages/gr3/ -lGR3 $(EXTRA_LD_FLAGS)
endif
SUBDIRS=


all: libalgorithm.so subdirs

libalgorithm.so: algorithm.c
	$(CC) -Wall -Wextra -fPIC $(CFLAGS) $(INCLUDES) -o $@ $< -shared $(LDFLAGS)

subdirs:
	for i in $(SUBDIRS); do make -C $$i all; done

clean:
	rm -f *.pyc *.pyo
	rm -f *.o *.so
	for i in $(SUBDIRS); do make -C $$i clean; done

