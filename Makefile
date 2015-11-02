SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)
MAC_APPS=mac-app mac-shallow-app

all: $(MAC_APPS) linuxpackages extensions doc

extensions:
	$(MAKE) -C src

mac-app:
	$(MAKE) -C packaging $@

mac-shallow-app: extensions
	$(MAKE) -C packaging $@

linuxpackages: extensions
	$(MAKE) -C packaging $@

doc:
	$(MAKE) -C doc

clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done

.PHONY: all extensions doc clean $(MAC_APPS) linuxpackages
