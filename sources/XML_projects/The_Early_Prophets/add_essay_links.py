from sources.functions import *

vtitle = "The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995"
everett = ["The Five Books of Moses, by Everett Fox, Leviticus, Part II; Ritual Pollution and Purification, Pollution from Tzaraat 2-4",
"The Five Books of Moses, by Everett Fox, Numbers, Part II; The Rebellion Narratives, On Bil'am 2-10"]
tanakh_refs = ["Leviticus 13", "Numbers 22:5-25:9"]
for refs in zip(tanakh_refs, everett):
	e, t = refs
	Link({"refs": [t, e],
                                       "auto": True, "type": "essay", "generated_by": "everett_fox_essay_links",
                                       "versions": [{"title": vtitle,
                                                     "language": "en"},
                                                    {"title": vtitle,
                                                     "language": "en"}],
                                       "displayedText": [{"en": t, "he": Ref(t).he_normal()},
                                                         {"en": e.replace(':', ';'), "he": Ref(e).he_normal()}]}).save()