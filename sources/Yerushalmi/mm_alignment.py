import django
django.setup()
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedTextArray
import yutil



###
# yutil.load_machon_mamre_data()
# yutil.load_guggenheimer_data()
errors = []
'''
for mesechet, index in [q for q in zip(yutil.mesechtot, yutil.jtindxes)][15:]:
    base_ref = Ref(index)  # text is depth 3.
    all_halachot = [halacha for perek in base_ref.all_subrefs() for halacha in perek.all_subrefs()]
    for halacha in all_halachot:
        perek_num = int(halacha.normal_section(0))
        halacha_num = int(halacha.normal_section(1))
        try:
            ma = yutil.MishnahAlignment(mesechet, perek_num, halacha_num)
            ma.run_compare()
        except IndexError:
            errors += [f"*** Failed to align {mesechet} {perek_num}:{halacha_num}"]
        except Exception as e:
            errors += [f"*** {str(e)} *** {mesechet} {perek_num}:{halacha_num}"]

for err in errors:
    print(err)
'''

def make_version_obj(index_title, chapter):
    return {
        "language": "he",
        "title": index_title,
        "versionSource": "https://www.mechon-mamre.org/b/r/r0.htm",
        "versionTitle": "Mechon-Mamre",
        "chapter": chapter
    }

for mesechet, index in [q for q in zip(yutil.mesechtot, yutil.jtindxes)]:
    base_ref = Ref(index)  # text is depth 3.
    version_content = []

    for perek in base_ref.all_subrefs():
        perek_num = int(perek.normal_section(0))
        perek_content = []

        for halacha in perek.all_subrefs():
            halacha_num = int(halacha.normal_section(1))

            try:
                ma = yutil.MishnahAlignment(mesechet, perek_num, halacha_num)
                ma.import_xlsx()
                perek_content += [ma.get_m_according_to_g()]
            except FileNotFoundError:
                perek_content += [[]]
                print(f"Missing {halacha.normal()}")
            except (KeyError, IndexError):
                perek_content += [[]]
                print(f"Mis-alignment of {halacha.normal()}")

        version_content += [perek_content]

    print(f"Creating {mesechet}")
    Version(make_version_obj(index, version_content)).save()



# For each Mesechet / Perek / Halacha
# Get segment / word count for each side
# Note page transitions for MM side
# Submit request to dicta
# save xls
# open xls and covert to data
# map MM onto G segments
# note page transition

