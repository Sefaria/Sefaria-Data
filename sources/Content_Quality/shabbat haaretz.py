from sources.functions import *
links = []
with open("Shabbat HaAretz - he - merged.csv", 'r') as f:
	for row in csv.reader(f):
		if row[0].startswith("Shabbat HaAretz, Laws of Shemitah "):
			rambam = row[0].replace("Shabbat HaAretz, Laws of Shemitah ", "Mishneh Torah, Sabbatical Year and the Jubilee ")
			rambam = ":".join(rambam.rsplit(":")[:-1])
			links.append({"refs": [row[0], rambam], "generated_by": "HAARETZ_to_rambam", "type": "Commentary",
										"auto": True})
post_link_in_steps(links, server="https://germantalmud.cauldron.sefaria.org")