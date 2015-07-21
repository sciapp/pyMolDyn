SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)

all: app
	@for subdir in ${SUBDIRS}; do \
		if [ -f $$subdir/Makefile ]; then \
			echo "make -C $$subdir"; \
			$(MAKE) -C $$subdir; \
		fi; \
	done

app:
	pwd
	PATH=/usr/local/bin:${PATH} gr shallow-appify.py -d src/ -i src/icon.png -e PATH PYTHONPATH DYLD_LIBRARY_PATH -o pyMolDyn.app src/startGUI.py

clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done
	rm -rf pyMolDyn.app
