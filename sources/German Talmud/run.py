import csv
import django
django.setup()
import os
from sefaria.model import *
files = [f for f in os.listdir(".") if f.endswith(".csv")]
for f in files:
  prev_ref = None
  print(f)
  with open(f, 'r') as open_f:
    for row in csv.reader(open_f):
      ref, comm = row
      try:
        ref = Ref(ref)
        if prev_ref and ref.prev_segment_ref(prev_ref):
          prev_ref = ref
        elif prev_ref:
          print("Problem at {}".format(ref))
          break

      except:
        pass
