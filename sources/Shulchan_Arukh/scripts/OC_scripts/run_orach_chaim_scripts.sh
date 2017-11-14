data_home=$(cd ../../../; pwd)
export PYTHONPATH=$PYTHONPATH:$data_home
python OC_base1.py
python OC_base2.py
python OC_base3.py
python taz.py
python eshel.py
