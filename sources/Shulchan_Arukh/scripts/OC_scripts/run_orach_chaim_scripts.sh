#!/usr/bin/env bash
data_home=$(cd ../../../; pwd)
export PYTHONPATH=$PYTHONPATH:$data_home
python startup.py
python OC_base1.py
python OC_base2.py
python OC_base3.py
python taz.py --run
python eshel.py --run
python ateret.py --run
python OC_parse_baerHaGoalah.py
