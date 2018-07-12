import csv,re
from sefaria.model import *




with open("pseud_dibur_hamatchil_examples.csv") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        base_ref = Ref(row["base ref"])
        comm_ref = Ref(row["commentary ref"])

        base_match = unicode(row["base text match"],'utf8').strip()
        comm_match = unicode(row["commentary text match"],'utf8').strip()

        base_tc = TextChunk(base_ref,"he")
        comm_tc = TextChunk(comm_ref,"he")

        base_text = base_tc.text.strip() if not base_ref.is_range() else u' '.join([seg for sec in base_tc.text for seg in sec])
        comm_text = comm_tc.text.strip()

        base_text = re.sub(ur'</?([^>])+>', u'\1', base_text)
        comm_text = re.sub(ur'</?([^>])+>', u'\1', comm_text)

        base_text = re.sub(ur'\s+',' ',base_text)
        comm_text = re.sub(ur'\s+',' ',comm_text)

        if (base_text.find(base_match) == -1) or (comm_text.find(comm_match) == -1):
            print "BAD",comm_ref,base_ref
        else:
            print "GOOD",comm_ref,base_ref