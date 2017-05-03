
SUBDIRS = calculation

all:
	for i in $(SUBDIRS); do make -C $$i PYLIBPATH=$(PYLIBPATH) EXTRA_LD_FLAGS=$(EXTRA_LD_FLAGS) all; done

clean:
	rm -f *.pyc *.pyo
	for i in $(SUBDIRS); do make -C $$i clean; done

