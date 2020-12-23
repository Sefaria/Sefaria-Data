from sources.functions import *
def convert_B0_to_bold(line):
    line = re.sub("@B0(.*?)@TX", "<b>\g<1></b>", line).replace("@B1", "")
    return line

with open("full text.txt", 'r') as f:
   for line in f:
       line = re.sub("<.*?>", "", line)
       line = convert_B0_to_bold(line)
       if "@MS" in line:
          pass
       elif "@DF" in line:
           matches = re.findall("<b>.*?</b>", line)
           if matches:
               first_match = matches[0]
               preceding_match = line.split(first_match)[0]
               preceding_match_is_daf = preceding_match.count(" ") == 2
               if preceding_match_is_daf:
                   dh = first_match

       else:
           match = re.search(": (<b>.*?</b>)", line)
           if match:
               dh = match.group(1)

