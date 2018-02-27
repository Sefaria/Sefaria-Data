#!/usr/bin/env bash

rm ../../Even_HaEzer.xml
python startup.py
python EH_base.py
python Taz.py --run
python EH_gra.py
python EH_Pithei_Teshuva.py
python EH_parse_BeerHaGolah.py
