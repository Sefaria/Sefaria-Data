import django

django.setup()

superuser_id = 171118
# import statistics
from sefaria.model import *




books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
                 "Judges", "I_Samuel", "II_Samuel", "I_Kings", "II_Kings",
                 "Ruth", "Esther"]
def fix():
    for book in books:
        segment_refs = library.get_index(book).all_segment_refs()
        for s_r in segment_refs:
            # en_version_text = s_r.text().text
            ru_version_text = s_r.text(vtitle="Russian Torah translation, by Dmitri Slivniak, Ph.D., edited by Dr. Itzhak Streshinsky [ru]")
            ru_version_text.text = ru_version_text.text.replace("<br>", "<br> ")
            ru_version_text.save()
            # print("hi")


if __name__ == '__main__':
    print("hello world")
    fix()
    print("end")