import django
django.setup()
from sefaria.system.database import db


sites_data = [
		{
				"name": "Tablet Magazine",
				"domains": ["tabletmag.com", "tabletmag.com.s3-website-us-east-1.amazonaws.com"],
				"bad_urls": [r"tabletmag\.com\/contributors\/", r"tabletmag\.com\.s3-website-us-east-1\.amazonaws.com\/contributors\/"],
			"normalization_rules": ["remove www"]
		},
		{
			"name": "Google",
			"is_whitelisted": False,
			"domains": ["googleusercontent.com"],
			"bad_urls": [r"webcache\.googleusercontent\.com", r"translate\.googleusercontent\.com", r"translate\.goog"]
		},
		{
			"name": "Dailympails",
			"is_whitelisted": False,
			"domains": ["dailympails.gq"],
			"bad_urls": [r"dailympails\.gq\/"]
		},
		{
			"is_whitelisted": False,
			"name": "Localhost",
			"domains": ['localhost',
								 'localhost:10063',
								 'localhost:3000',
								 'localhost:4005',
								 'localhost:8000',
								 'localhost:8080'],
			"bad_urls": [r"http(s)?:\/\/localhost(:\d+)?"]
		},
    {
			"name":           "My Jewish Learning",
			"domains":        ["myjewishlearning.com"],
			"normalization_rules": ["use https", "remove www"],
			"bad_urls": [r"myjewishlearning\.com\/\?post_type=evergreen"]
	},
	{
			"name":           "Virtual Beit Midrash",
			"domains":        ["etzion.org.il", "vbm-torah.org", "torah.etzion.org.il", "haretzion.linnovate.co.il"],
			"title_branding": ["vbm haretzion"],
		  "normalization_rules": ["remove www"]

	},
	{
			"name":           "Rabbi Sacks",
			"domains":        ["rabbisacks.org"],
			"normalization_rules": ["use https", "remove www"],
			"bad_urls": [r"rabbisacks\.org\/(.+\/)?\?s="]
	},
	{
			"name":           "Halachipedia",
			"domains":        ["halachipedia.com"],
			"normalization_rules": ["use https", "remove www", "remove mediawiki params"],
		  "bad_urls": [r"halachipedia\.com\/index\.php\?search=", # Halachipedia search results
            			r"halachipedia\.com\/index\.php\?diff="]   # Halachipedia diff pages]
	},
	{
			"name":           "Torah In Motion",
			"domains":        ["torahinmotion.org"],
		"normalization_rules": ["remove www"]

	},
	{
			"name":           "The Open Siddur Project",
			"domains":        ["opensiddur.org"],
		"exclude_from_tracking": ".header"
	},
	{
			"name":           "בית הלל",
			"domains":        ["beithillel.org.il"],
			"title_branding": ["בית הלל - הנהגה תורנית קשובה"],
		  "normalization_rules": ["remove www"]

	},
	{
			"name":                   "ParshaNut",
			"domains":                ["parshanut.com"],
			"title_branding":         ["PARSHANUT"],
			"initial_title_branding": True,
			"normalization_rules":    ["use https"],
	},
	{
			"name":            "Real Clear Daf",
			"domains":         ["realcleardaf.com"],
		"normalization_rules": ["remove www"]

	},
	{
			"name":           "NACH NOOK",
			"domains":        ["nachnook.com"],
		"normalization_rules": ["remove www"]

	},
	{
			"name":           "Congregation Beth Jacob, Redwood City",
			"domains":        ["bethjacobrwc.org"],
			"title_branding": ["CBJ"]
	},
	{
			"name":    "Amen V'Amen",
			"domains": ["amenvamen.com"],
	},
	{
			"name":    "Rabbi Sharon Sobel",
			"domains": ["rabbisharonsobel.com"],
		"normalization_rules": ["remove www"]

	},
	{
			"name":    "The Kosher Backpacker",
			"domains": ["thekosherbackpacker.com"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "WebYeshiva",
			"domains": ["webyeshiva.org"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "Tradition Online",
			"domains": ["traditiononline.org"],
			"normalization_rules": ["remove mediawiki params"],
		"bad_urls": [r"traditiononline\.org\/page\/\d+\/"]
	},
	{
			"name": "Partners in Torah",
			"domains": ["partnersintorah.org"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "The Lehrhaus",
			"domains": ["thelehrhaus.com"]
	},
	{
			"name": "סִינַי",
			"domains": ["sinai.org.il"],
			"title_branding": ["הדף היומי ב15 דקות - שיעורי דף יומי קצרים בגמרא"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": 'אתר לבנ"ה - קרן תל"י',
			"domains": ["levana.org.il"],
			"title_branding": ["אתר לבנה מבית קרן תל&#039;&#039;י", "אתר לבנה מבית קרן תל''י"]  # not sure how HTML escape characters are handled. Including both options.
	},
	{
			"name": 'Judaism Codidact',
			"domains": ["judaism.codidact.com"],
			"title_branding": ["Judaism"],
			"initial_title_branding": True,
			"normalization_rules": ["remove sort param"],
		  "bad_urls": [r"judaism\.codidact\.com\/.+\/edit",
            r"judaism\.codidact\.com\/.+\/history",
						r"judaism\.codidact\.com\/",
						r"judaism\.codidact\.com\/#",
						r"judaism\.codidact\.com\/mod\/*",
						r"judaism\.codidact\.com\/users\/*",
  					r"judaism\.codidact\.com\/users\/",
						r"judaism\.codidact\.com\/?page=\d+",
					  r"judaism\.codidact\.com\/categories\/d+",
						r"judaism\.codidact\.com\/.+\/suggested-edit\/",
            r"judaism\.codidact\.com\/.+\/posts\/new\/",
            r"judaism\.codidact\.com\/questions\/d+",  # these pages redirect to /posts
            r"judaism\.codidact\.com\/users\/"]
	},

	{
			"name": "The Jewish Theological Seminary",
			"domains": ["jtsa.edu"],
			"normalization_rules": ["remove url params", "remove www"],
		"bad_urls": [r"www\.jtsa.edu\/search\/index\.php"]
	},
	{
			"name": "Ritualwell",
			"domains": ["ritualwell.org"],
			"normalization_rules": ["remove www"],
	},
	{
			"name": "Jewish Exponent",
			"domains": ["jewishexponent.com"],
		  "bad_urls": [r"jewishexponent\.com\/page\/\d"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "The 5 Towns Jewish Times",
			"domains": ["5tjt.com"],
  		"normalization_rules": ["remove www"]

	},
	{
			"name": "Hebrew College",
			"domains": ["hebrewcollege.edu"],
		  "bad_urls": [r"hebrewcollege\.edu\/blog\/(author|category|tag)\/",
									 r"hebrewcollege\.edu\/blog\/(author|tag)\/"]
	},
	{
			"name": "מכון הדר",
			"domains": ["mechonhadar.org.il"],
			"bad_urls": [r"mechonhadar\.org\.il\/envatoq"],
				"exclude_from_tracking": ".elementor-34"

	},
	{
			"name": "Pardes Institute of Jewish Studies",
			"domains": ["pardes.org", "elmad.pardes.org"],
			"title_branding": ["Elmad Online Learning Torah Podcasts, Online Jewish Learning"]
	},
	{
			"name": "Yeshivat Chovevei Torah",
			"domains": ["yctorah.org"],
			"title_branding": ["Torah Library of Yeshivat Chovevei Torah", "Rosh Yeshiva Responds"],
		  "bad_urls": [r"psak\.yctorah\.org\/?$",
            r"psak\.yctorah\.org\/(category|about|source)\/",  # archives
            r"psak\.yctorah\.org\/sitemap_index\.xml$", r"library\.yctorah\.org\/series\/"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "Rabbi Jeff Fox (Rosh ha-Yeshiva, Yeshivat Maharat)",
			"domains": ["roshyeshivatmaharat.org"],
			"title_branding": ["Rosh Yeshiva Maharat"],
			"bad_urls": [r"roshyeshivatmaharat.org\/(author|category|tag)\/"]
	},
	{
			"name": "Cleveland Jewish News",
			"domains": ["clevelandjewishnews.com"],
			"title_branding": ["clevelandjewishnews.com"],
		  "bad_urls": [r"clevelandjewishnews\.com$",
            r"clevelandjewishnews\.com\/news\/"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "Rabbi Noah Farkas",
			"domains": ["noahfarkas.com"],
			"title_branding": ["Rabbi Noah farkas"]
	},
	{
			"name": "Reconstructing Judaism",
			"domains": ["reconstructingjudaism.org"],
		"bad_urls": [r"reconstructingjudaism\.org\/taxonomy\/",
            r"reconstructingjudaism\.org\/search\/"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "The Institute for Jewish Ideas and Ideals",
			"domains": ["jewishideas.org"],
			"title_branding": ["jewishideas.org"],
		  "bad_urls": [r"jewishideas\.org\/search\/",
            r"jewishideas\.org\/articles\/"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "The Jewish Virtual Library",
			"domains": ["jewishvirtuallibrary.org"],
			"normalization_rules": ["use https", "remove url params", "remove www"],
	},
	{
			"name": "Lilith Magazine",
			"domains": ["lilith.org"],
		  "bad_urls": [r"lilith\.org\/\?gl=1\&s=",                  # Lilith Magazine search results
            r"lilith\.org\/(tag|author|category)\/"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "Torah.org",
			"domains": ["torah.org"],
		"bad_urls": [r"https://torah\.org$"]

	},
	{
			"name": "Sinai and Synapses",
			"domains": ["sinaiandsynapses.org"],
	},
	{
			"name": "Times of Israel Blogs",
			"domains": ["blogs.timesofisrael.com"],
			"title_branding": ["The Blogs"],
		"exclude_from_tracking": ".ob-widget-section"
	},
	{
			"name": "The Jewish Standard",
			"domains": ["jewishstandard.timesofisrael.com"],
		  "exclude_from_tracking": ".ob-widget-section"
	},
	{
			"name": "Rav Kook Torah",
			"domains": ["ravkooktorah.org"],
			"normalization_rules": ["remove www"]
	},
	{
			"name": "YUTorah Online",
			"domains": ["yutorah.org", "yutorah.com", "yutorah.net"],
			"initial_title_branding": True,
		"bad_urls": [r"yutorah\.org\/search\/",
            r"yutorah\.org\/searchResults\.cfm",
            r"yutorah\.org\/\d+\/?$",  # year pages
            r"yutorah\.org\/users\/",
            r"yutorah\.org\/daf\.cfm\/?$"],
		"normalization_rules": ["remove www"]
	},
	{
			"name": "Hadran",
			"domains": ["hadran.org.il"],
		"bad_urls": [r"test\.hadran\.org\.il",
								 r"hadran\.org\.il\/he\/?$",
								 r"hadran\.org\.il\/he\/(masechet|מסכת)\/",
								 r"hadran\.org\.il\/daf-yomi\/$"],
		"exclude_from_tracking": ".nav-links, .hard_sub_header"

	},
	{
		"name": "סיון רהב-מאיר",
		"domains": ["sivanrahavmeir.com"],
		"bad_urls": [r"sivanrahavmeir\.com\/?$"],
		"normalization_rules": ["remove www"]
	},
	{
			"name": "Julian Ungar-Sargon",
			"domains": ["jyungar.com"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "Aish HaTorah",
			"domains": ["aish.com", "aish.co.il", "aishlatino.com", "aish.fr"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "Jewschool",
			"domains": ["jewschool.com"],
		"bad_urls": [r"jewschool\.com\/page\/"]
	},
	{
			"name": "T'ruah",
			"domains": ["truah.org"],
		  "bad_urls": [r"truah\.org\/\?s=",
            r"truah\.org\/(holiday|page|resource-types)\/"]
	},
	{
	    "name": "929",
	    "domains": ["929.org.il"],
	    "title_branding": ["929 – תנך ביחד", "Tanakh - Age Old Text, New Perspectives"],
	    "initial_title_branding": True,
		"normalization_rules": ["remove www"]

	},
	{
			"name": "נאמני תורה ועבודה",
			"domains": ["toravoda.org.il"],
		"bad_urls": [ r"toravoda\.org\.il\/%D7%90%D7%99%D7%A8%D7%95%D7%A2%D7%99%D7%9D-%D7%97%D7%9C%D7%95%D7%A4%D7%99\/"] # Neemanei Torah Vavoda list of past events]
	},
	{
			"name": "Ohr Torah Stone",
			"domains": ["ots.org.il"],
			"title_branding": ["אור תורה סטון"],
		  "bad_urls": [r"ots\.org\.il\/news\/",
            r"ots\.org\.il\/.+\/page\/\d+\/",
            r"ots\.org\.il\/tag\/.+",
						 r"ots\.org\.il\/parasha\/",
						 r"ots\.org\.il\/torah-insights\/",
						 r"ots\.org\.il\/new-home-"]

	},
	{
			"name": "Jewish Action",
			"domains": ["jewishaction.com"],
	},
	{
			"name": "Rabbi Johnny Solomon",
			"domains": ["rabbijohnnysolomon.com"],
		  "bad_urls": [r"rabbijohnnysolomon.com$",
            r"rabbijohnnysolomon.com\/shiurim\/$",
            r"rabbijohnnysolomon.com\/shiurim\/parasha\/$",
            r"rabbijohnnysolomon.com\/shiurim\/halacha\/$"]
	},
	{
			"name": "Moment Magazine",
			"domains": ["momentmag.com"],
	},
	{
			"name": "Orthodox Union (OU Torah)",
			"domains": ["ou.org", "outorah.org", "oukosher.org"],
			"title_branding": ["Jewish Holidays", "OU Holidays", "OU", "OU Torah", "OU Life"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "Judaism 101 (JewFAQ)",
			"domains": ["jewfaq.org"],
			"title_branding": ["Judaism 101:"],
			"initial_title_branding": True,
			"normalization_rules": ["remove url params", "remove www"],
		"bad_urls": [            r"jewfaq\.org\/search\.shtml"] # Judaism 101, Search the Glossary and Index]
	},
	{
			"name": "Jewish Women's Archive",
			"domains": ["jwa.org"],
		"bad_urls": [r"jwa\.org\/encyclopedia\/author\/",  # tends to have articles by author that have snippets from article
            r"jwa\.org\/encyclopedia\/content\/"]
	},
	{
			"name": "The Wexner Foundation",
			"domains": ["wexnerfoundation.org"],
		"normalization_rules": ["remove www"]
	},
	{
			"name": "Jewish Drinking",
			"domains": ["jewishdrinking.com"],
	},
	{
			"name": "Avodah",
			"domains": ["avodah.net"],
		"bad_urls": [r"avodah\.net\/(blog|category|tag)/"]
	},
	{
			"name": "TorahWeb.org",
			"domains": ["torahweb.org"],
   		"normalization_rules": ["remove www"]

	},
	{
			"name": "AskHalacha",
			"domains": ["askhalacha.com"],
		"bad_urls": [r"askhalacha\.com\/?$",
            r"askhalacha\.com\/qas\/?$"]
	},
	{
			"name": "Yeshiva.co",
			"domains": ["yeshiva.co"],
			"title_branding": ["Ask the rabbi | Q&A | yeshiva.co", "Beit Midrash | Torah Lessons | yeshiva.co", "yeshiva.co"],
		  "bad_urls": [r"yeshiva\.co\/?$",
									 r"yeshiva\.co\/not-found$",
            r"yeshiva\.co\/404\/404.asp",
            r"yeshiva\.co\/(ask|midrash)\/?$",
            r"yeshiva\.co\/(calendar|tags|dedication|errorpage)\/?",  # it seems anything under calendar is not an article
            r"yeshiva\.co\/midrash\/(category|rabbi)\/?"],
		"normalization_rules": ["remove www"],
		"exclude_from_tracking": ".error-container, .print-hide"

	},
	{
			"name": "מחלקי המים",
			"domains": ["mayim.org.il"],
		"bad_urls": [r"mayim\.org\.il\/?$"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "The Kabbalah of Time",
			"domains": ["kabbalahoftime.com"],
			"initial_title_branding": True,
		"bad_urls": [            r"kabbalahoftime\.com\/?$",
            r"kabbalahoftime\.com\/\d{4}\/?$",  # page that aggregates all articles for the year
            r"kabbalahoftime\.com\/\d{4}\/\d{2}\/?$"],  # page that aggregates all articles for the month]
		"normalization_rules": ["remove www"]

	},
	{
			"name": "Jewish Contemplatives",
			"domains": ["jewishcontemplatives.blogspot.com"],
			"initial_title_branding": True,
		"bad_urls": [r"jewishcontemplatives\.blogspot\.com\/?$"]
	},
	{
			"name": "Orayta",
			"domains": ["orayta.org"],
			"normalization_rules": ["use https", "remove www"],
		"bad_urls": [r"orayta\.org\/orayta-torah\/orayta-byte-parsha-newsletter"]
	},
	{
			"name": "Rabbi Efrem Goldberg",
			"domains": ["rabbiefremgoldberg.org"],
			"normalization_rules": ["use https", "remove www", "remove url params"],
	},
	{
			"name": "Jewish Encyclopedia",
			"domains": ["jewishencyclopedia.com", "jewishencyclopedia.herokuapp.com"],
			"title_branding": ["JewishEncyclopedia.com"],
			"normalization_rules": ["remove url params", "use https", "remove www"],
		"bad_urls": [r"jewishencyclopedia\.com\/(directory|contribs|search)"]
	},
	{
			"name": "Wilderness Torah",
			"domains": ["wildernesstorah.org"],
	},
	{
			"name": "Or HaLev",
			"domains": ["orhalev.org"],
			"normalization_rules": ["use https", "remove www"],
		"bad_urls": [r"orhalev\.org\/blogs\/parasha-and-practice\/?$",
            r"orhalev\.org\/blogs\/tag\/"]
	},
	{
			"name": "Talmudology",
			"domains": ["talmudology.com"],
			"normalization_rules": ["use https", "remove www"],
		"bad_urls": [
            r"talmudology\.com\/?$",
            r"talmudology\.com\/[^\/]+$"]  # seems everything at the top level is not an article]
	},
	{
			"name": "S and P Sephardi Community",
			"domains": ["sephardi.org.uk"],
		"bad_urls": [r"sephardi\.co\.uk\/(category|community|tag|test)\/"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "זיכרון בספר",
			"domains": ["mevoot.michlala.edu"],
			"normalization_rules": ["use https", "remove www", "remove all params after id"]
	},
	{
			"name": "Evolve",
			"domains": ["evolve.reconstructingjudaism.org"],
	},
	{
			"name": "The Amen Institute",
			"domains": ["theameninstitute.com"],
		"bad_urls": [ r"theameninstitute\.com\/?$",
            r"theameninstitute\.com\/category\/whats-new-at-the-amen-institute\/?$"]
	},
	{
			"name": "Office of the Chief Rabbi",
			"domains": ["chiefrabbi.org"],
		"bad_urls": [r"chiefrabbi\.org\/?(\?post_type.+)?$",  # post_type are pages that seem to by filtered lists
            r"chiefrabbi\.org\/(all-media|communities|education|maayan-programme)\/?$",
            r"chiefrabbi\.org\/(dvar-torah|media_type)\/?"]  # archives]
	},
	{
			"name": "Sapir Journal",
			"domains": ["sapirjournal.org"],
	},
	{
			"name": "Justice in the City",
			"domains": ["justice-in-the-city.com"],
		"bad_urls": [r"justice-in-the-city\.com\/?$",
            r"justice-in-the-city\.com\/(category|page)\/"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": "American Jewish University",
			"domains": ["aju.edu"],
		"bad_urls": [r"aju\.edu\/(faculty|search|taxonomy)\/",
            r"aju\.edu\/miller-intro-judaism-program\/learning-portal\/glossary\/",
            r"aju\.edu\/ziegler-school-rabbinic-studies\/our-torah\/back-issues\/\d+$"
            r"aju\.edu\/ziegler-school-rabbinic-studies\/torah-resource-center\/"
            r"aju\.edu\/ziegler-school-rabbinic-studies\/blogs\/?$"],
		"normalization_rules": ["remove www"]

	},
	{
			"name": 'התנ"ך',
			"domains": ["hatanakh.com"],
			"title_branding": ["התנך"],
			"normalization_rules": ["use https", "remove www"],
		  "bad_urls": [r"hatanakh\.com\/?#?$",
            r"hatanakh\.com\/\/(en|es)$",  # home page?
            r"hatanakh\.com(\/(en|es))?\/?#?(\?.+)?$",  # a sledgehammer. gets rid of odd url params on homepage + spanish chapter pages
            r"hatanakh\.com\/\.[^/]+$",  # strange private pages
            r"hatanakh\.com\/((en|es)\/)?(tanach|search|taxonomy|tags|%D7%9E%D7%97%D7%91%D7%A8%D7%99%D7%9D|%D7%93%D7%9E%D7%95%D7%99%D7%95%D7%AA|%D7%A0%D7%95%D7%A9%D7%90%D7%99%D7%9D)\/",  # topic, author and character pages
            r"hatanakh\.com\/((en|es)\/)?search",
            r"hatanakh\.com\/\?(chapter|custom|gclid|parasha)=",  # chapter pages
            r"hatanakh\.com\/(en|es)?\/home",  # other chapter pages?
            r"hatanakh\.com\/((en|es)\/)?(articles|daily|node)\/?$",
            r"hatanakh\.com\/((en|es)\/)?(articles|lessons)\?(page|arg|tanachRef(\[|%5B)\d+(\]|%5D))=",
            r"hatanakh\.com\/((en|es)\/)?(daily)?\/?\?(chapter|custom|gclid|parasha)=",
            r"hatanakh\.com\/es\/\?biblia="]
  }
]




collection = db.websites
db.drop_collection(collection)
keys = set()
domains = []
names = []
for site_data in sites_data:
	assert site_data["name"] not in names
	names.append(site_data["name"])
	domains += site_data["domains"]
	if "is_whitelisted" not in site_data:
		site_data["is_whitelisted"] = True
	collection.insert_one(site_data)
	for k in site_data:
		keys.add(k)
collection.create_index("date")


if len(set(domains)) != len(domains):  # make sure no duplicate domains
	domains = sorted(domains)
	set_domains = sorted(list(set(domains)))
	for x, y in zip(domains, set_domains):
		print("{} vs {}".format(x, y))


