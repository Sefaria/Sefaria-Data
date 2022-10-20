import django

django.setup()

from sefaria.model import *

# Re GM: In the end, the priority for each version needs to be an integer.
# Practically, you just need to make sure that the Berlin version is higher priority
# than the Goldshmidt for every masechet. The way I would approach it is:

# For each masechet
#           Load both all versions for masechet. You can do this using index.versionSet() which
#           returns a VersionSet of the versions on that index
#
#           Checking that Berlin is higher priority than Goldshmidt
#
#            If not, set Goldshmidt's priority higher than Berlin's while making sure it is lower (i.e. switch)
#            than any version that was originally higher priority (meaning, don't make Goldshmidt the same
#            priority as a previously higher priority version).

if __name__ == '__main__':

    mishnah_indexes = library.get_indexes_in_category("Mishnah", full_records=True)
    for index in mishnah_indexes:
        print(index)
        for v in index.versionSet():
            if v.versionTitle == 'Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]':
                v.priority = 0.5
                v.save()
            elif v.versionTitle == "Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]":
                v.priority = 0.25
                v.save()