
SUBDIRS = computation gui util visualization config core statistics

all:
	for i in $(SUBDIRS); do make -C $$i PYLIBPATH=$(PYLIBPATH) EXTRA_LD_FLAGS=$(EXTRA_LD_FLAGS) all; done

app_extension_modules: clean all

clean:
	rm -f *.pyc *.pyo
	for i in $(SUBDIRS); do make -C $$i clean; done

