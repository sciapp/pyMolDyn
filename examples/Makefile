SUBDIRS=$(shell find . -type d -d 1)

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
