# encoding=utf-8
import sys
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import django
django.setup()
from sefaria.model import *
import time

from docx import Document

if __name__ == "__main__":
    start = time.time()
    raem = Document(u'{}.docx'.format(u'תוספות רבי עקיבא איגר על המשניות'))
    raem_list = []
    during_bold = False
    for para in raem.paragraphs:
        raem_list.append(u'@')
        for run in para.runs:
            if type(run.text) == unicode:
                if not during_bold and run.bold:
                    raem_list.append(u'<b>{}'.format(run.text))
                    during_bold = True
                elif during_bold and not run.bold:
                    raem_list.append(u'</b>{}'.format(run.text))
                    during_bold = False
                else:
                    raem_list.append(run.text)
            else:
                raem_list.append(run.text)

    raem_string = u''.join(raem_list)


    end = time.time()
    print end-start

