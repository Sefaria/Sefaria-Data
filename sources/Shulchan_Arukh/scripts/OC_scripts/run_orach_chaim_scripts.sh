#!/usr/bin/env bash
data_home=$(cd ../../../; pwd)
export PYTHONPATH=$PYTHONPATH:$data_home
echo $PYTHONPATH
echo "startup"
python startup.py
echo "OC_base1"
python OC_base1.py
echo "OC_base2"
python OC_base2.py
echo "OC_base3"
python OC_base3.py
echo "taz"
python taz.py --run
echo "eshel"
python eshel.py --run
echo "ateret"
python ateret.py --run
echo "OC_parse_baerHaGoalah"
python OC_parse_baerHaGoalah.py
echo "hok_yaakov"
python hok_yaakov.py --run
python shaarei_teshuvah.py
