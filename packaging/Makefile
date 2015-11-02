SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)
MAC_APPS = mac-app mac-shallow-app
DISTROS = all

all: $(MAC_APPS) linuxpackages

mac-app:
	$(MAKE) -C mac_os_x app

mac-shallow-app:
	$(MAKE) -C mac_os_x shallow-app

linuxpackages:
	$(MAKE) -C linux DISTROS=all all

clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done

.PHONY: all clean $(MAC_APPS) linuxpackages
