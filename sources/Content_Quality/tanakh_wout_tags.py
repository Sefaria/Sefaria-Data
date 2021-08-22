from sources.functions import *
en_vtitle = "The Holy Scriptures: A New Translation (JPS 1917)"
with open("tanakh.csv", 'w') as f:
	writer = csv.writer(f)
	for book in library.get_indexes_in_category("Tanakh"):
		print(book)
		for ref in library.get_index(book).all_segment_refs():
			en_tc = bleach.clean(TextChunk(ref, lang='en', vtitle=en_vtitle).text, strip=True, tags=[], attributes=[])
			he_tc = bleach.clean(ref.text('he').text, strip=True, tags=[], attributes=[])
			if "<" in he_tc or "<" in en_tc:
				print(ref)
			writer.writerow([ref.normal(), he_tc, en_tc])