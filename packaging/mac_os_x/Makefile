SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)
MAC_APPS=app shallow-app

all: $(MAC_APPS)

app:
	gr shallow-appify/shallow-appify.py -d ../../src/ -i ../../src/icon.png --conda conda_requirements.txt --conda-channels https://conda.anaconda.org/jheinen --extension-makefile ../../src/Makefile -o pyMolDyn.app ../../src/startGUI.py

shallow-app:
	PATH=/usr/local/bin:${PATH} gr shallow-appify/shallow-appify.py -d ../../src/ -i ../../src/icon.png -e PATH PYTHONPATH DYLD_LIBRARY_PATH -o pyMolDyn-shallow.app ../../src/startGUI.py

clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done
	rm -rf pyMolDyn.app pyMolDyn-shallow.app

.PHONY: all clean $(MAC_APPS)