import django
django.setup()
from sefaria.model import *
import yutil


###
yutil.load_machon_mamre_data()
yutil.load_guggenheimer_data()

# For each Mesechet / Perek / Halacha
# Get segment / word count for each side
# Note page transitions for MM side
# Submit request to dicta
# save xls
# open xls and covert to data
# map MM onto G segments
# note page transition

