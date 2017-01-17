# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
from sefaria.model import *
from functions import *

if __name__ == "__main__":
    '''loop through each volume getting text of each mitzvah and posting it '''
    volume_one = (365, "Volume One", 0)
    volume_two = (248, "Volume Two", 0)
    volumes = [volume_one, volume_two]
    for volume in volumes:
        for i in range(volume[0]):
            if i < volume[2]:
                continue
            index = library.get_index("SeMaG")
            ref = Ref("SeMaG, {} {}".format(volume[1], i+1))
            en_text = ref.text('en').text
            he_text = ref.text('he').text
            he_text = {
                "text": he_text,
                "language": "he",
                "versionTitle": "Munkatch, 1901",
                "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637"
            }
            ref_str = ref.normal().replace(":", ".").replace(" ", "_")
            print ref_str
            post_text(ref_str, he_text)
            if len(en_text) > 0:
                en_text = {
                "text": en_text,
                "language": "en",
                "versionTitle": "Sefaria Community Translation",
                "versionSource": "http://www.sefaria.org/"
                }
                post_text(ref_str, en_text)