
SUBDIRS = 

all:
	for i in $(SUBDIRS); do make -C $$i all; done
	latexmk -pdf master.tex

clean:
	rm -f *.spec *.log *.fdb_latexmk *.aux *.out *.fls *.toc *.pdf *.synctex.gz 
	for i in $(SUBDIRS); do make -C $$i clean; done

