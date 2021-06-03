from sources.functions import *
i = get_index_api("Bnei Machshava Tova", server="https://www.sefaria.org")
i["categories"] = ["Chasidut", "Other Chasidut Works"]
post_index(i, server="https://www.sefaria.org")