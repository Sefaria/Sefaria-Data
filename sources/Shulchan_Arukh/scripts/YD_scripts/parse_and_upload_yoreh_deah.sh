#!/usr/bin/env bash

if [ $# -gt 0 ]; then
    server="$1"
else
    server="http://deah.sandbox.sefaria.org"
fi

./run_yoreh_deah.sh
python upload.py -s "${server}" -n
python upload.py -t "Siftei Kohen" -s "${server}" -n
python upload.py -t "Be'er HaGolah" -s "${server}" -n
python upload.py -t "Beur HaGra" -s "${server}" -n
python upload.py -t "Turei Zahav" -s "${server}" -n
python upload.py -t "Pithei Teshuva" -s "${server}" -n
python upload.py -t "Torat HaShlamim" -s "${server}" -n -a
python upload.py -t "Nekudat HaKesef" -s "${server}" -n -a

curl -X POST --data-urlencode 'payload={"text": "Finished Uploading Yoreh Deah"}' ${SLACK_URL}
