SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)
LINUX_PACKAGES=debian centos

all: $(LINUX_PACKAGES)

debian:

centos:

clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done

.PHONY: all clean $(LINUX_PACKAGES)
