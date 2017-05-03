
SUBDIRS = computation gui util visualization config core statistics

all:
	for i in $(SUBDIRS); do make -C $$i PYLIBPATH=$(PYLIBPATH) EXTRA_LD_FLAGS=$(EXTRA_LD_FLAGS) all; done

EXTRA_LD_FLAGS = -Wl,-rpath,/usr/local/gr/lib
app_extension_modules: clean all

clean:
	rm -f *.pyc *.pyo
	for i in $(SUBDIRS); do make -C $$i clean; done

