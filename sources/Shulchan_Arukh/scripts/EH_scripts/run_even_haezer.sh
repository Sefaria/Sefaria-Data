#!/usr/bin/env bash

rm ../../Even_HaEzer.xml
python startup.py
python EH_base.py
echo "Taz"
python Taz.py --run
echo "Beur HaGra"
python EH_gra.py
echo "Pithei Teshuva"
python EH_Pithei_Teshuva.py
echo "Beer HaGolah"
python EH_parse_BeerHaGolah.py
