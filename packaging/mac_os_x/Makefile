SUBDIRS=$(shell find . -mindepth 1 -maxdepth 1 -type d)
MAC_APPS=app shallow-app

all: $(MAC_APPS)

app:
	mkdir self-contained-app
	gr shallow-appify/shallow-appify.py -d ../../src/ -i ../../src/icon.png --conda conda_requirements.txt --conda-channels https://conda.anaconda.org/jheinen --extension-makefile ../../src/Makefile -o self-contained-app/pyMolDyn.app ../../src/startGUI.py
	./create-dmg/create-dmg --volname pyMolDyn --window-size 800 400 --background dmg_background.png --icon pyMolDyn.app 200 200 --hide-extension pyMolDyn.app --app-drop-link 600 200 pyMolDyn.dmg self-contained-app

shallow-app:
	mkdir shallow-app
	PATH="/usr/local/bin:/usr/bin:/bin" PYTHONPATH="/usr/local/gr/lib/python" gr shallow-appify/shallow-appify.py -d ../../src/ -i ../../src/icon.png -e PATH PYTHONPATH -o shallow-app/pyMolDyn.app ../../src/startGUI.py

clean:
	@for subdir in ${SUBDIRS}; do \
                if [ -f $$subdir/Makefile ]; then \
                        echo "make -C $$subdir clean"; \
                        $(MAKE) -C $$subdir clean; \
                fi; \
        done
	rm -rf self-contained-app shallow-app pyMolDyn.dmg

.PHONY: all clean $(MAC_APPS)
