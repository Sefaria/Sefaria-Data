# SeferHaAggadah
Convert a PDF version of Sefer HaAggadda to text in order to extract the embedded sources within. 

First obtain a legal copy of the PDF Sefer HaAgaddah in Hebrew

Then use ghostscript to convert the pdf into an xml file with this command:

$ gs -dNOPAUSE -sDEVICE=txtwrite -dFirstPage=28 -dLastPage=639 -dTextFormat=1 -sOutputFile=part1.xml -q part1.pdf -c quit

where, 

-dFirstPage is the page of the pfd that you want to start converting and -dLastPage is the page you want to end.

-q is the same of the pdf to convert

-isOutputFile is the name of the file where the conversion will go

Then Run ExtractSources.py

The program should take about a minute to run (each xml file has around 5 million lines..one line per letter in the PDF file)

You should end up with a file that has all the sources organized by section.




