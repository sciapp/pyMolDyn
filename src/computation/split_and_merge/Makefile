
SUBDIRS = domain_centers util

all:
	for i in $(SUBDIRS); do make -C $$i all; done

clean:
	for i in $(SUBDIRS); do make -C $$i clean; done

