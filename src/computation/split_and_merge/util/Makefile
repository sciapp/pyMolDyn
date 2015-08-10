
SUBDIRS = numpy_extension

all:
	for i in $(SUBDIRS); do make -C $$i PYLIBPATH=$(PYLIBPATH) all; done

clean:
	rm -rf *.pyo *.pyc
	for i in $(SUBDIRS); do make -C $$i clean; done

