
SUBDIRS = 

all:
	for i in $(SUBDIRS); do make -C $$i all; done

clean:
	rm -f *.pyc *.pyo
	rm -f config.cfg config.spec
	for i in $(SUBDIRS); do make -C $$i clean; done

