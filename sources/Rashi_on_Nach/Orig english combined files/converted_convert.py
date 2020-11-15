import os
for f in os.listdir('.'):
    cmd = """iconv -f ISO-8859-8 -t UTF-8 < "./{}" > "./converted_{}" -c""".format(f, f)
    os.popen(cmd)