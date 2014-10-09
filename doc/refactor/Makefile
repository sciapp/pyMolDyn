TARGETS=master.pdf checklist.pdf

.PHONY: all clean

all: ${TARGETS}

clean:
	rm -f ${TARGETS} *.aux *.log *.toc *.out *.fls *.fdb_latexmk

master.pdf: master.tex data.tex file.tex calculation.tex control.tex visualization.tex
	latexmk -pdf $<

checklist.pdf: checklist.tex
	latexmk -pdf $<
