SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)

all: mac-app mac-shallow-app

mac-app:
	$(MAKE) -C mac_os_x app

mac-shallow-app:
	$(MAKE) -C mac_os_x shallow-app

clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done

.PHONY: all mac-app mac-shallow-app clean
