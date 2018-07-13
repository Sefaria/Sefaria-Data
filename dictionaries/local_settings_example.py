# encoding=utf-8

import os
import sys

SEFARIA_PROJECT_PATH = "Path to your Sefaria-Project"
SEFARIA_DATA_PATH = "Path to your Sefaria-Data"
sys.path.insert(0, os.path.abspath(SEFARIA_PROJECT_PATH))
sys.path.insert(1, os.path.abspath(SEFARIA_DATA_PATH))
os.environ["DJANGO_SETTINGS_MODULE"] = "sefaria.settings"
