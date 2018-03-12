#!/usr/bin/env bash

if [ $# -gt 0 ]; then
    server="$1"
else
    server="http://localhost:8000"
fi
echo "Even HaEzer"
python upload.py -a -s ${server}
echo "Beur HaGra"
python upload.py -a -t "Beur HaGra" -s ${server}
echo "Pithei Teshuva"
python upload.py -a -t "Pithei Teshuva" -s ${server}
echo "Be'er HaGolah"
python upload.py -a -t "Be'er HaGolah" -s ${server}
echo "Turei Zahav"
python upload.py -a -t "Turei Zahav" -s ${server}
