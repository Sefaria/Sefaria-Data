## How to run modify_tanakh_links.py



```bash
POD=<POD TO RUN ON>
kubectl cp linking_utilities $POD:/app/scripts
kubectl exec -it $POD -- bash
# on pod
export PYTHONPATH="/app/scripts:$PYTHONPATH"
pip install numpy num2words
cd scripts/linking_utilities/citation_disambiguator
python modify_tanakh_links.py data/unambiguous_links.csv data/errors.csv
```