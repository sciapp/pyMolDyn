
SUBDIRS = split_and_merge

all:
	for i in $(SUBDIRS); do make -C $$i PYLIBPATH=$(PYLIBPATH) all; done

clean:
	rm -f *.pyc *.pyo
	for i in $(SUBDIRS); do make -C $$i clean; done

