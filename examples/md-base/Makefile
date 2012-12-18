EXAMPLES=$(shell ls *.example.c | sed s/.c$$//)

all: libmd-base ${EXAMPLES}
	
%.example: %.example.c ../../lib/md-base/libmd-base.a
	gcc -o $@ $< -L../../lib/md-base -I../../lib/md-base/ -I../../lib/md-base/container/ -lmd-base
		
../../lib/md-base/libmd-base.a: libmd-base

libmd-base:
	$(MAKE) -C ../../lib/md-base
	
clean:
	rm -f *.example
