SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)
MAC_APPS=mac-app mac-shallow-app
LINUX_PACKAGES=debian-package centos-package

all: $(MAC_APPS) $(LINUX_PACKAGES)

mac-app:
	$(MAKE) -C mac_os_x app

mac-shallow-app:
	$(MAKE) -C mac_os_x shallow-app

debian-package:
	$(MAKE) -C linux debian

centos-package:
	$(MAKE) -C linux centos

clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done

.PHONY: all clean $(MAC_APPS) $(LINUX_PACKAGES)
