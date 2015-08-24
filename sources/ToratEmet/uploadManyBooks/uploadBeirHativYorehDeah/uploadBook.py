from postFile2 import *

def postBook(title, filename):
	index = {
	"title": title,
	"titleVariants": ["Beer Hetev on Shulchan Arukh, Yoreh De'ah", "Be'ir Hetev on Shulchan Arukh, Yoreh De'ah", "Ba'er Hetev on Shulchan Arukh, Yoreh De'ah","Beir Hetev on Shulchan Arukh, Yoreh De'ah", "Baer Hetev on Shulchan Arukh, Yoreh De'ah" ],
	"heTitle" : "באר היטב יורה דעה",
	"heTitleVariants" : [],
	"sectionNames": ["Siman" , "Se'if Katan"], 
	"categories": ["Halakhah", "Shulchan Arukh"],
	}
	textIndex = {
		"versionTitle": "Torat Emet 357",
		"versionSource":  "http://www.toratemetfreeware.com/index.html?downloads",
		"language": "he",	
	}
	actuallyPost = False; # False=> outputting file; True=> post to site
	useRealSite = False; # False=> dev site; True=> real site
	postBookIndex = True; #do False for old book in their DB, and do True for new book.
	symbolAtLevel = ['~', '!'] #put symbols where 'NL' means that NL is the lowest level. COMMON symbols: [ '~','^', '@', '$', '!', '#'] that start a new Chapter/Paragraph/etc in ToratEmet
	displayHeaderSymbols = []	# Put symbols (but not NL) that you want to display header into displayHeaderSymbol with bigger first. ex. displayHeaderSymbol = [ '@', '~']	
	createHeader = ['~'] #these are the headers for which you want to create a headers.csv with
	headerAttr = [[1,1]] # put in the attributes for the headers in the format: [displayNum , displayLevelType (ex. daf)] . ex. if using 2 header syms = [[1,0], [0,0]]
	useAsNumberForLocation = ['!'] #typically used for commentary (usually ['!']), where not every line is there but there is only a commentary on some lines.
	postSifKatans = True # if you want to post Sif Katans (which are contained within a line of TE)
	commentary = True #if this is a commentary on something make it true. <book title> on <thing it's a comment on> is assumed to be the title of this book
	postFile2(filename, index, textIndex,symbolAtLevel, actuallyPost, useRealSite,postBookIndex, displayHeaderSymbols, createHeader, headerAttr, useAsNumberForLocation, postSifKatans, commentary)
	

	

title = "Be'er Hetev on Shulchan Arukh, Yoreh De'ah";
filename = "051_באר_היטב_יורה_דעה.txt";
postBook(title, filename)

"""
Comments/Changes/Problems:
168 and 169 are really the same thing, so it makes the numbers all off. So I just copied 168 and made it into 169 (this is what they did for the reguar shalchan aruach).

198.48 is having a weird thing... b/c of the *	. So I changed the line 4579 to:

{{{{מו}}}}(מה*) [ [[טבילה אחרת. ]] בלא ברכה. ב''ח וש''ך]: )מו( [[להחמיר. ]] מיהו אם אנסה חברתה ואטבלה כונה דחברתה כונה מעליותא היא לכ''ע הכי אמרי' בש''ס חולין דף ל''א: {{{{מז}}}} [[אלו. ]] כגון כלב או חמור או ע''ה או עובד כוכבים או חזיר או סוס או מצורע וכיוצא בהן כ''כ בש''ד אבל ברוקח וכל בו איתא שאם פגע בה סוס תעלה ותשמש שבניה עומדים נאה בדבורן שומעין ומבינין לומדים תורה ואינם משכחין וממעטין בשינה ולא עוד אלא שאימתן מוטלת על הבריות כו' עכ''ל וגרסינן בפסחים האי מאן דפגע באיתתא בעידנא דסלקה מטבילת מצוה אי איהו קדים ומשמש אחדא ליה לדידיה רוח זנונית ואי איהי קדמה ומשמשה אחדא לה לדידה רוח זנונית מאי תקנתיה לימא הכי שופך בוז על נדיבים ויתעם בתוהו לא דרך והוא בתהלים ק''ז והכי מייתי לה ברוקח אבל בתולדות אהרן לא ציין מקרא דשופך בוז על נדיבים אלא ומזיח אפיקים רפה באיוב י''ב נראה שלא היה גורס בש''ס שופך בוז וכו' ובילקוט מייתי ש''ס זה בתהלים ובאיוב הלכך נמרינהו לתרווייהו עכ''ל הש''ך:

217.16 -- 
changed line 5033 from 
{{{{טז}}}} [[בחמשת. ]] הם חטה ושעורה כוסמין שבולת שועל ושיפון:
to:
{{{{טו}}}} [[בחמשת. ]] הם חטה ושעורה כוסמין שבולת שועל ושיפון:
b/c it was doubled up and the incorrect number.


297 has 297.5... that's a shame. I have to deal with that. I changed the letter values so that it can all fit into 297


"""
