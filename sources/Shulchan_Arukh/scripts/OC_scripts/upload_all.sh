#!/usr/bin/env bash

if [ $# -gt 0 ]; then
    server="$1"
else
    server="http://localhost:8000"
fi
echo "Orach Chayim"
python upload.py -a -s ${server}
echo "Turei Zahav"
python upload.py -a -t "Turei Zahav" -s ${server}
echo "Eshel Avraham"
python upload.py -a -t "Eshel Avraham" -s ${server}
echo "Ateret Zekenim"
python upload.py -a -t "Ateret Zekenim" -s ${server}
echo "Chok Yaakov"
python upload.py -a -t "Chok Yaakov" -s ${server}
echo "Sha'arei Teshuvah"
python upload.py -a -t "Sha'arei Teshuvah" -s ${server}
echo "Be'er HaGolah"
python upload.py -a -t "Be'er HaGolah" -s ${server}
