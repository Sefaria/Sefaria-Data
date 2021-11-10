import django
django.setup()
from research.knowledge_graph.named_entity_recognition.ner_tagger import LiteralTextWalker

def test_bold_finder():
    text = """Having explained the latter part of the verse in Isaiah, the Gemara turns to the beginning of that same verse. <b>“Then shall the lambs feed as in their pasture</b> [<b><i>kedavram</i>].” Menashya bar Yirmeya said that Rav said: As was said about them</b> [<b><i>kamedubar bam</i>],</b> i.e., as the prophet promised. To <b>what</b> prophecy does the verse refer with the expression <b>“as was said about them”? Abaye said:</b> It is referring to the continuation of the verse: <b>“And the ruins of the fat ones shall wanderers eat.” Rava said to him</b> that this cannot be: <b>Granted, were it written</b> only <b>“the ruins</b> of the fat ones,” it would be possible to explain <b>as you said. Now that it is written “and the ruins,”</b> with the addition of the word “and,” this indicates that <b>it states something else,</b> and the verse contains two separate prophecies."""
    spans = LiteralTextWalker.get_literal_ranges(text, "<b>.+?</b>")
    assert text[spans[1][0]:spans[1][1]] == "<b><i>kedavram</i>].” Menashya bar Yirmeya said that Rav said: As was said about them</b>"