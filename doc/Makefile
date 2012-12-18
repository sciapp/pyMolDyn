PDFFILE=master.pdf
TEXFILES=master.tex
TEXFILES+=packages.tex

${PDFFILE}: ${TEXFILES}
	pdflatex master
	pdflatex master
    
clean:
	rm -f ${PDFFILE} # resulting pdf file
	rm -f *.aux # auxiliary file
	rm -f *.log # log file
	rm -f *.toc # table of contents
