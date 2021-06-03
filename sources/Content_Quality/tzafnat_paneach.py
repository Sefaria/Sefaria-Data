
from sources.functions import *
links = get_links("Tzafnat Pa'neach on Torah", server="https://www.sefaria.org")
links = [l for l in links if "Numbers" in l["anchorRef"]]
print(len(links))
post_link_in_steps(links, step=4, server="https://www.sefaria.org")