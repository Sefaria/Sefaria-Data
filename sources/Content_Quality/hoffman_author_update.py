import django

django.setup()

from sefaria.model import *

mishnayot = VersionSet({"versionTitle": "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]"})

for mishnah in mishnayot:
    print(mishnah.title)
    mishnah.versionNotes = "Ordnung Seraïm, übers. und erklärt von Ascher Samter. 1887.<br>Ordnung Moed, von Eduard Baneth. 1887-1927.<br>Ordnung Naschim, von Marcus Petuchowski u. Simon Schlesinger. 1896-1933.<br>Ordnung Nesikin, von David Hoffmann. 1893-1898.<br>Ordnung Kodaschim, von John Cohn. 1910-1925.<br>Ordnung Toharot, von David Hoffmann, John Cohn und Moses Auerbach. 1910-1933."
    mishnah.save()