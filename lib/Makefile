SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)

all:
	@for subdir in ${SUBDIRS}; do \
		if [ -f $$subdir/Makefile ]; then \
			echo "make -C $$subdir"; \
			$(MAKE) -C $$subdir; \
		fi; \
	done
clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done
