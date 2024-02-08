import django

django.setup()
from sefaria.model import *
import re
from tqdm import tqdm
import bleach

probs = {}
for b in library.get_indexes_in_corpus("Tanakh"):
    for ref in tqdm(library.get_index(b).all_segment_refs()):
        tc = TextChunk(ref, lang='he', vtitle="Miqra according to the Masorah")
        text = bleach.clean(tc.text, strip=True, tags=[]).strip().replace(":", "")
        matches = re.findall("((\[.{1,10}\])(\S+))", text)
        for m in matches:
            # m = bleach.clean(m, strip=True, tags=[]).strip()
            #brackets_word, after_word = m
            probs[ref] = m[0]
{Ref('Amos 8:4'): '[עֲנִיֵּי־]אָֽרֶץ׃', Ref('Daniel 2:38'): '[אַ֨נְתְּ־]ה֔וּא',
 Ref('Daniel 4:14'): '[עֲלַֽהּ]׃', Ref('Daniel 4:16'): '[לְעָרָֽךְ]׃',
 Ref('Daniel 4:19'): '[אַנְתְּ־]ה֣וּא', Ref('Daniel 5:13'): '[אַנְתְּ־]ה֤וּא', Ref('Daniel 5:21'): '[עֲלַֽהּ]׃', Ref('Deuteronomy 5:10'): '[מִצְוֺתָֽי]׃',
 Ref('Exodus 37:8'): '[קְצוֹתָֽיו]׃', Ref('Ezekiel 9:5'): '[אַל־]תָּחֹ֥ס', Ref('Ezekiel 16:51'): '[עָשִֽׂית]׃',
 Ref('Ezekiel 21:28'): '[כִּקְסׇם־]שָׁוְא֙', Ref('Ezekiel 24:2'): '[כְּתׇב־]לְךָ֙',
 Ref('Ezekiel 37:22'): '[יִֽהְיוּ־]עוֹד֙', Ref('Ezekiel 44:3'): '[לֶאֱכׇל־]לֶ֖חֶם',
 Ref('Ezekiel 46:9'): '[יֵצֵֽא]׃', Ref('Ezra 2:50'): '[נְפוּסִֽים]׃',
 Ref('Ezra 10:29'): '[וְרָמֽוֹת]׃', Ref('Ezra 10:35'): '[כְּלֽוּהוּ]׃',
 Ref('Genesis 27:3'): '[צָֽיִד]׃', Ref('Hosea 8:12'): '[אֶ֨כְתׇּב־]ל֔וֹ',
 Ref('Hosea 9:16'): '[בַֽל־]יַעֲשׂ֑וּן', Ref('Hosea 10:10'): '[עוֹנֹתָֽם]׃',
 Ref('I Chronicles 1:46'): '[עֲוִֽית]׃', Ref('I Chronicles 7:31'): '[בִרְזָֽיִת]׃',
 Ref('I Chronicles 11:20'): '[וְלוֹ־]שֵׁ֖ם', Ref('I Chronicles 18:10'): '[לִשְׁאׇל־]ל֨וֹ',
 Ref('I Chronicles 24:24'): '[שָׁמִֽיר]׃', Ref('I Kings 5:17'): '[רַגְלָֽי]׃',
 Ref('I Kings 17:14'): '[תֵּת־]יְהֹוָ֛ה', Ref('I Samuel 5:9'): '[טְחֹרִֽים]׃',
 Ref('I Samuel 19:18'): '[בְּנָיֽוֹת]׃', Ref('I Samuel 20:24'): '[אֶל־]הַלֶּ֖חֶם',
 Ref('I Samuel 22:15'): '[לִשְׁאׇל־]ל֥וֹ', Ref('I Samuel 25:3'): '[כָֽלִבִּֽי]׃',
 Ref('I Samuel 28:8'): '[קָסֳמִי־]נָ֥א', Ref('II Chronicles 11:18'): '[בַּת־]יְרִימ֖וֹת',
 Ref('II Chronicles 36:14'): '[לִמְעׇל־]מַ֔עַל', Ref('II Kings 4:5'): '[מוֹצָֽקֶת]׃',
 Ref('II Kings 6:25'): '[דִּב־]יוֹנִ֖ים', Ref('II Kings 11:20'): '[הַמֶּֽלֶךְ]׃',
 Ref('II Kings 14:6'): '[יוּמָֽת]׃', Ref('II Kings 16:17'): '[אֶת־]הַכִּיֹּ֔ר',
 Ref('II Kings 23:10'): '[בֶן־]הִנֹּ֑ם', Ref('II Samuel 14:7'): '[שִׂים־]לְאִישִׁ֛י',
 Ref('II Samuel 14:22'): '[עַבְדֶּֽךָ]׃', Ref('II Samuel 18:3'): '[לַעְזֽוֹר]׃',
 Ref('II Samuel 21:6'): '[יֻתַּן־]לָ֜נוּ', Ref('II Samuel 22:15'): '[וַיָּהֹֽם]׃'
    , Ref('II Samuel 22:33'): '[דַּרְכִּֽי]׃', Ref('II Samuel 23:8'): '[אֶחָֽת]׃',
 Ref('Isaiah 10:32'): '[בַּת־]צִיּ֔וֹן', Ref('Isaiah 26:20'): '[יַעֲבׇר־]זָֽעַם׃',
 Ref('Isaiah 44:17'): '[יִסְגׇּד־]ל֤וֹ', Ref('Isaiah 44:24'): '[מֵאִתִּֽי]׃',
 Ref('Isaiah 65:7'): '[אֶל־]חֵיקָֽם׃', Ref('Jeremiah 3:19'): '[תָשֽׁוּבִי]׃',
 Ref('Jeremiah 5:7'): '[אֶֽסְלַֽח־]לָ֔ךְ', Ref('Jeremiah 6:21'): '[וְאָבָֽדוּ]׃', Ref('Jeremiah 22:6'): '[נוֹשָֽׁבוּ]׃', Ref('Jeremiah 33:8'): '[לְכׇל־]עֲוֺנֽוֹתֵיהֶם֙', Ref('Jeremiah 37:4'): '[הַכְּלֽוּא]׃', Ref('Jeremiah 48:7'): '[יַחְדָּֽיו]׃', Ref('Jeremiah 48:21'): '[מֵיפָֽעַת]׃', Ref('Jeremiah 49:36'): '[עֵילָֽם]׃', Ref('Jeremiah 52:11'): '[בֵֽית־]הַפְּקֻדֹּ֖ת', Ref('Jeremiah 52:31'): '[הַכְּלֽוּא]׃', Ref('Job 7:1'): '[עֲלֵי־]אָ֑רֶץ', Ref('Job 9:30'): '[בְמֵי־]שָׁ֑לֶג', Ref('Job 19:29'): '[שַׁדּֽוּן]׃', Ref('Job 41:4'): '[לוֹ־]אַחֲרִ֥ישׁ', Ref('Joshua 9:7'): '[אֶֽכְרׇת־]לְךָ֥', Ref('Lamentations 1:6'): '[מִבַּת־]צִיּ֖וֹן', Ref('Nahum 1:3'): '[וּגְדׇל־]כֹּ֔חַ', Ref('Nahum 2:1'): '[לַעֲבׇר־]בָּ֥ךְ', Ref('Nehemiah 10:20'): '[נֵיבָֽי]׃', Ref('Numbers 23:13'): '[לְכָה־]נָּ֨א', Ref('Proverbs 11:3'): '[יְשָׁדֵּֽם]׃', Ref('Proverbs 17:27'): '[יְקַר־]ר֝֗וּחַ', Ref('Proverbs 18:17'): '[וּבָֽא־]רֵ֝עֵ֗הוּ', Ref('Proverbs 19:7'): '[לוֹ־]הֵֽמָּה׃', Ref('Proverbs 19:16'): '[יָמֽוּת]׃', Ref('Proverbs 19:19'): '[גְּֽדׇל־]חֵ֭מָה', Ref('Proverbs 22:8'): '[יִקְצׇר־]אָ֑וֶן', Ref('Proverbs 22:11'): '[טְהׇר־]לֵ֑ב', Ref('Proverbs 22:14'): '[יִפׇּל־]שָֽׁם׃', Ref('Proverbs 23:24'): '[יִשְׂמַח־]בּֽוֹ׃', Ref('Proverbs 27:24'): '[וָדֽוֹר]׃', Ref('Psalms 9:13'): '[עֲנָוִֽים]׃', Ref('Psalms 10:12'): '[עֲנָוִֽים]׃', Ref('Psalms 38:21'): '[רׇֽדְפִי־]טֽוֹב׃', Ref('Psalms 60:7'): '[וַעֲנֵֽנִי]׃', Ref('Psalms 71:12'): '[חֽוּשָׁה]׃', Ref('Psalms 89:29'): '[אֶשְׁמׇר־]ל֣וֹ', Ref('Ruth 4:6'): '[לִגְאׇל־]לִ֔י', Ref('Zechariah 11:2'): '[הַבָּצִֽיר]׃', Ref('Zephaniah 2:7'): '[שְׁבִיתָֽם]׃'}

found = ['ל֔וֹ', 'נָּ֨א', 'לְךָ֥']
print(probs)
