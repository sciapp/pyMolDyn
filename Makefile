SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)

all: mac-app mac-shallow-app extensions doc

extensions:
	$(MAKE) -C src

mac-app:
	$(MAKE) -C packaging mac-app

mac-shallow-app: extensions
	$(MAKE) -C packaging mac-shallow-app

doc:
	$(MAKE) -C doc

clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done

.PHONY: all extensions mac-app mac-shallow-app doc clean
