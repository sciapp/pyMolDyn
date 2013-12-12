
SUBDIRS = numpy_extension

all:
	for i in $(SUBDIRS); do make -C $$i all; done

clean:
	for i in $(SUBDIRS); do make -C $$i clean; done

