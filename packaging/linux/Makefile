SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)
ALL_DISTROS = debian centos fedora suse
ifeq ($(DISTROS),all)
	override DISTROS = $(ALL_DISTROS)
endif

all: linuxpackages

linuxpackages:
	@which fpm >/dev/null 2>&1 || \
	( echo "FATAL: fpm could not be found in PATH.\n       Visit https://github.com/jordansissel/fpm for more information on fpm."; exit 1 )
ifndef DISTROS
	@./create_package.sh
else
	@for DISTRO in $(DISTROS); do \
		./create_package.sh "$${DISTRO}" || break; \
	done
endif

clean:
	for DIR in $(ALL_DISTROS); do \
		rm -rf $${DIR}; \
	done
	rm -f *.deb *.rpm
	@for subdir in ${SUBDIRS}; do \
		if [ -f $$subdir/Makefile ]; then \
			echo "make -C $$subdir clean"; \
			$(MAKE) -C $$subdir clean; \
		fi; \
	done

.PHONY: all clean linuxpackages
