
SUBDIRS = split_and_merge

all:
	for i in $(SUBDIRS); do make -C $$i all; done

clean:
	for i in $(SUBDIRS); do make -C $$i clean; done

