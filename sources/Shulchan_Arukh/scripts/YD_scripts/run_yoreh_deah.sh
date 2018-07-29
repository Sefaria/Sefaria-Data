#!/usr/bin/env bash

rm ././../../Yoreh_Deah.xml
python ./startup.py
python ./YD_base.py
echo "Shach"
python ./YD_Shach.py
echo "Taz"
python ./YD_Taz.py
echo "Pithei Teshuva"
python ./YD_Pithei.py
echo "Beur HaGra"
python ./YD_gra.py
echo "Torat HaShalmim"
python ./YD_torat_hashalmim.py
echo "Beer HaGolah"
python ./beer_hagolah.py
echo "Nekudat HaKesef"
python ./nekudat_haKesef.py
curl -X POST --data-urlencode 'payload={"text": "Finished Parsing Yoreh Deah"}' ${SLACK_URL}
