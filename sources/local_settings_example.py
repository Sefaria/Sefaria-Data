"""
Local Settings Example file for Sefaria-Data scripts
Copy this file to "local_settings.py" and import values as needed.
e.g.:

import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)

from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "settings"
from sefaria.model import *

"local_settings.py" is excluded from this Git repo.
"""

# In scripts you can add this value to your Python path so that you can
# import from sefaria, if this path is not already set in your environment
SEFARIA_PROJECT_PATH = "/path/your/copy/of/Sefaria-Project"

SEFARIA_SERVER = "http://localhost:8000"

API_KEY = "your API key"
