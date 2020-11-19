import os
from sources.functions import *
from time import sleep
def insert_bold_italics(line):
   line = line#.replace(chr(147), 'open"').replace(chr(148), 'close"')
   bold = False
   italics = False
   new_words = []
   for word in line.split():
      if word == "<b>":
         bold = True
         new_words.append("<b>")
      elif word == "<i>":
         italics = True
         new_words.append("<i>")
      elif word == "cb8":
         if bold:
            new_words.append("</b>")
            bold = False
         elif italics:
            assert not bold
            new_words.append("</i>")
            italics = False
         else:
            pass
      else:
         new_words.append(word)
   return " ".join(new_words)




versionTitles = """Isaiah
---
Isaiah, English translation by I.W. Slotki, Soncino Press, 1949
https://www.nli.org.il/en/books/NNL_ALEPH002642658/NLI

---

Jeremiah
---
Jeremiah, English translation by H. Freedman, Soncino Press, 1949
https://www.nli.org.il/en/books/NNL_ALEPH002579486/NLI

---

Ezekiel
---
Ezekiel, English translation by S. Fisch, Soncino Press, 1950
https://www.nli.org.il/en/books/NNL_ALEPH002642688/NLI

---

The Twelve Prophets
---
The Twelve Prophets, English translation by A. Cohen, Soncino Press, 1948
https://www.nli.org.il/en/books/NNL_ALEPH002644211/NLI

---

Psalms
---
The Psalms, English translation by A. Cohen, Soncino Press, 1945
https://www.nli.org.il/en/books/NNL_ALEPH002643011/NLI

---

Proverbs
---
Proverbs, English translation by A. Cohen, Soncino Press, 1945
https://www.nli.org.il/en/books/NNL_ALEPH002643042/NLI

---

Job
---
Job, English translation by Victor E. Reichert, Soncino Press, 1946
https://www.nli.org.il/en/books/NNL_ALEPH002643064/NLI

---

The Five Megilloth
---
The Five Megilloth, English translation by A. Cohen, Soncino Press, 1946
https://www.nli.org.il/en/books/NNL_ALEPH002644163/NLI

---

Daniel, Ezra and Nehemiah
---
Daniel, Ezra and Nehemiah, English translation by Judah J. Slotki, Soncino Press, 1951
https://www.nli.org.il/en/books/NNL_ALEPH002644183/NLI

---

Chronicles
---
Chronicles, English translation by I.W. Slotki, Soncino Press, 1952
https://www.nli.org.il/en/books/NNL_ALEPH002644317/NLI""".split("---")
def get_vtitle(desired_title):
    curr = ""
    desired_title = desired_title.replace("Rashi on ", "")
    if desired_title.startswith("Chronicles"):
        desired_title = "Chronicles"
    elif desired_title in ["Daniel", "Ezra", "Nehemiah"]:
        desired_title = "Daniel, Ezra and Nehemiah"
    elif desired_title in ["Song of Songs", "Ruth", "Esther", "Lamentations", "Ecclesiastes"]:
        desired_title = "The Five Megilloth"

    for i, title in enumerate(versionTitles):
        if i % 2 == 1:
            if curr == desired_title:
                return [t for t in title.splitlines() if t.strip()]
        else:
            curr = title.strip()
    else:
        return ["The Twelve Prophets, English translation by A. Cohen, Soncino Press, 1948", "https://www.nli.org.il/en/books/NNL_ALEPH002644211/NLI"]

def parse(lines):
   text = {}
   chapter = 0
   verse = 0
   prev_line_match = ""
   for i, line in enumerate(lines):
      line = line.strip().replace("<b> ", "<b>")
      if i < 2 or line.strip() == "":
         continue

      chapter_m = re.search("^<b>Chapter (.*?)</b>$", line)
      verse_m = re.search("^<b>(\d+)</b>$", line)
      line_match = re.search("^<b>(.*?)</b>$", line)

      if chapter_m:
         chapter = int(chapter_m.group(1))
         text[chapter] = {}
      elif verse_m:
         verse = int(verse_m.group(1))
         text[chapter][verse] = []
         prev_line_match = ""
      elif line_match:
         if line_match.group(1).strip() == prev_line_match.strip():
            text[chapter][verse][-1] += "<br/>" + line_match.group(0) + " "
         else:
            text[chapter][verse].append(line_match.group(0) + " ")
         prev_line_match = line_match.group(1)
      else:
         if text[chapter][verse] == []:
            text[chapter][verse] = [line]
         else:
            text[chapter][verse][-1] += line
   for ch in text:
      text[ch] = convertDictToArray(text[ch])
   text = convertDictToArray(text)
   return text

def strip_extra_bold_tags(line):
   new_line = ""
   for subline in line.split("<b>"):
      if "</b>" not in subline:
         continue
      if len(subline.split("</b>")) > 2:
          subline = subline.replace("</b>", "?/b", 1)
          subline = subline.replace("</b>", "").replace("?/b", "</b>")
          assert len(subline.split("</b>")) == 2
      subline = "<b>" + subline
      new_line += subline

   return new_line

def striprtf(text):
   pattern = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)", re.I)
   # control words which specify a "destionation".
   destinations = frozenset((
      'aftncn','aftnsep','aftnsepc','annotation','atnauthor','atndate','atnicn','atnid',
      'atnparent','atnref','atntime','atrfend','atrfstart','author','background',
      'bkmkend','bkmkstart','blipuid','buptim','category','colorschememapping',
      'colortbl','comment','company','creatim','datafield','datastore','defchp','defpap',
      'do','doccomm','docvar','dptxbxtext','ebcend','ebcstart','factoidname','falt',
      'fchars','ffdeftext','ffentrymcr','ffexitmcr','ffformat','ffhelptext','ffl',
      'ffname','ffstattext','field','file','filetbl','fldinst','fldrslt','fldtype',
      'fname','fontemb','fontfile','fonttbl','footer','footerf','footerl','footerr',
      'footnote','formfield','ftncn','ftnsep','ftnsepc','g','generator','gridtbl',
      'header','headerf','headerl','headerr','hl','hlfr','hlinkbase','hlloc','hlsrc',
      'hsv','htmltag','info','keycode','keywords','latentstyles','lchars','levelnumbers',
      'leveltext','lfolevel','linkval','list','listlevel','listname','listoverride',
      'listoverridetable','listpicture','liststylename','listtable','listtext',
      'lsdlockedexcept','macc','maccPr','mailmerge','maln','malnScr','manager','margPr',
      'mbar','mbarPr','mbaseJc','mbegChr','mborderBox','mborderBoxPr','mbox','mboxPr',
      'mchr','mcount','mctrlPr','md','mdeg','mdegHide','mden','mdiff','mdPr','me',
      'mendChr','meqArr','meqArrPr','mf','mfName','mfPr','mfunc','mfuncPr','mgroupChr',
      'mgroupChrPr','mgrow','mhideBot','mhideLeft','mhideRight','mhideTop','mhtmltag',
      'mlim','mlimloc','mlimlow','mlimlowPr','mlimupp','mlimuppPr','mm','mmaddfieldname',
      'mmath','mmathPict','mmathPr','mmaxdist','mmc','mmcJc','mmconnectstr',
      'mmconnectstrdata','mmcPr','mmcs','mmdatasource','mmheadersource','mmmailsubject',
      'mmodso','mmodsofilter','mmodsofldmpdata','mmodsomappedname','mmodsoname',
      'mmodsorecipdata','mmodsosort','mmodsosrc','mmodsotable','mmodsoudl',
      'mmodsoudldata','mmodsouniquetag','mmPr','mmquery','mmr','mnary','mnaryPr',
      'mnoBreak','mnum','mobjDist','moMath','moMathPara','moMathParaPr','mopEmu',
      'mphant','mphantPr','mplcHide','mpos','mr','mrad','mradPr','mrPr','msepChr',
      'mshow','mshp','msPre','msPrePr','msSub','msSubPr','msSubSup','msSubSupPr','msSup',
      'msSupPr','mstrikeBLTR','mstrikeH','mstrikeTLBR','mstrikeV','msub','msubHide',
      'msup','msupHide','mtransp','mtype','mvertJc','mvfmf','mvfml','mvtof','mvtol',
      'mzeroAsc','mzeroDesc','mzeroWid','nesttableprops','nextfile','nonesttables',
      'objalias','objclass','objdata','object','objname','objsect','objtime','oldcprops',
      'oldpprops','oldsprops','oldtprops','oleclsid','operator','panose','password',
      'passwordhash','pgp','pgptbl','picprop','pict','pn','pnseclvl','pntext','pntxta',
      'pntxtb','printim','private','propname','protend','protstart','protusertbl','pxe',
      'result','revtbl','revtim','rsidtbl','rxe','shp','shpgrp','shpinst',
      'shppict','shprslt','shptxt','sn','sp','staticval','stylesheet','subject','sv',
      'svb','tc','template','themedata','title','txe','ud','upr','userprops',
      'wgrffmtfilter','windowcaption','writereservation','writereservhash','xe','xform',
      'xmlattrname','xmlattrvalue','xmlclose','xmlname','xmlnstbl',
      'xmlopen',
   ))
   # Translation of some special characters.
   specialchars = {
      'par': '\n',
      'sect': '\n\n',
      'page': '\n\n',
      'line': '\n',
      'tab': '\t',
      'emdash': u'\u2014',
      'endash': u'\u2013',
      'emspace': u'\u2003',
      'enspace': u'\u2002',
      'qmspace': u'\u2005',
      'bullet': u'\u2022',
      'lquote': u'\u2018',
      'rquote': u'\u2019',
      'ldblquote': u'\201C',
      'rdblquote': u'\u201D',
   }
   stack = []
   ignorable = False       # Whether this group (and all inside it) are "ignorable".
   ucskip = 1              # Number of ASCII characters to skip after a unicode character.
   curskip = 0             # Number of ASCII characters left to skip
   out = []                # Output buffer.
   for match in pattern.finditer(text):
      word,arg,hex,char,brace,tchar = match.groups()
      if brace:
         curskip = 0
         if brace == '{':
            # Push state
            stack.append((ucskip,ignorable))
         elif brace == '}':
            # Pop state
            ucskip,ignorable = stack.pop()
      elif char: # \x (not a letter)
         curskip = 0
         if char == '~':
            if not ignorable:
                out.append(u'\xA0')
         elif char in '{}\\':
            if not ignorable:
               out.append(char)
         elif char == '*':
            ignorable = True
      elif word: # \foo
         curskip = 0
         if word in destinations:
            ignorable = True
         elif ignorable:
            pass
         elif word in specialchars:
            out.append(specialchars[word])
         elif word == 'uc':
            ucskip = int(arg)
         elif word == 'u':
            c = int(arg)
            if c < 0: c += 0x10000
            if c > 127: out.append(chr(c))
            else: out.append(chr(c))
            curskip = ucskip
      elif hex: # \'xx
         if curskip > 0:
            curskip -= 1
         elif not ignorable:
            c = int(hex,16)
            if c > 127: out.append(chr(c))
            else: out.append(chr(c))
      elif tchar:
         if curskip > 0:
            curskip -= 1
         elif not ignorable:
            out.append(tchar)
   return ''.join(out)

if __name__ == "__main__":
   text = {}
   found = set()
   for f in os.listdir("."):
       if f.startswith("converted"):
           new_f = "final_"+f.replace(".rtf", '.txt')
           lines = []
           with open(f, 'r') as open_f:
               line = open_f.read()
               bold_tags = ["\\cb14\\", "\\cb13\\", "\\cb10\\"]
               italic_tags = "\\cb11\\"
               open_quotes = 'open"'
               close_quotes = '"close'
               for bold in bold_tags:
                  line = line.replace(bold, " <b>")
               line = line.replace("\\cb11\\", " <i>")
               line = line.replace("\\cb8\\", " cb8 ")
               line = insert_bold_italics(line)
               # line = re.sub(" <b>(.*?) cb8 ", "<b>\g<1></b>", line)
               # line = re.sub(" <i>(.*?) cb8 ", "<i>\g<1></i>", line)


               #
               #    line = line.replace(bold, "?B?")
               # line = line.replace("cb8\\", "?/B?")
               line = striprtf(line) #.replace("/B?", "</b>\n").replace("B?", "<b>")
               sublines = strip_extra_bold_tags(line).replace("<b>", "\n<b>").replace("</b>", "</b>\n").splitlines()
               for l in sublines:
                  if "&" in line:
                     found.add(line.split("&")[0].split()[-1])
                  lines.append(l.replace("\x91", "").replace("\x92", "").replace("Pirk&","Pirkei "))
           text[f] = parse(lines)
           with open(new_f, 'w') as open_f:
              open_f.writelines(lines)

   starting = True
   start = "Song of Songs"
   for f in text.keys():
      orig_title = f.replace("converted_", "").replace(".rtf", "")
      if orig_title == start:
         starting = True
      if not starting:
         continue

      title = "Rashi on {}".format(orig_title)

      # root = JaggedArrayNode()
      # root.add_primary_titles(title, he_title)
      # root.add_structure(["Chapter", "Verse", "Paragraph"])
      # root.key = title
      # root.validate()
      # index = {
      #    "base_text_titles": [orig_title],
      #    "dependence": "Commentary",
      #    "base_text_mapping": "many_to_one",
      #    "title": title, 'schema': root.serialize(), "categories": ["Tanakh", "Commentary", "Rashi"]}
      # Index(index).save()
      versionTitle, versionSource = get_vtitle(title)
      send_text = {
         "text": text[f],
         "language": "en",
         "versionTitle": versionTitle,
         "versionSource": versionSource
      }
      try:
         #post_index(index)
         post_text(title, send_text)
         sleep(1)
      except Exception as e:
         print(e)

   print(found)