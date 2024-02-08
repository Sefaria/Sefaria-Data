import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
import re
import requests
# import requests_cache
# requests_cache.install_cache('my_cache', expire_after=3600*24*14)
from bs4 import BeautifulSoup
# from sefaria.helper.schema import insert_last_child, reorder_children
# from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
# from sefaria.helper.category import create_category
# from sefaria.system.database import db

judges_18_duplicate = """1 В те времена не было царя в Израиле,  а колено Дана искало себе надел, где жить,   потому что  все еще не получило себе надела в Израиле.  
2 И послали сыны Дана от своих семейств пять человек из их краев, храбрецов из Цоръа и Эштаоля, чтобы разведать и исследовать землю, и сказали им:  идите исследуйте землю.   И пришли они в горы Эфрайима, и (добрались до) дома Михи, и заночевали там. 3 В доме у Михи  они узнали голос юноши  -левита, и зашли внутрь, и сказали ему: Кто привел тебя сюда? Что ты здесь делаешь? Какое у тебя тут (дело)? 4 Тот сказал им:  так и так поступил со мной Миха, он  нанял меня,   и я у него священником. 5 И сказали ему:  спроси у Бога,   чтобы нам знать, будет ли наша дорога удачной. 6 И отвечал им священник: идите с миром – видна Господу та дорога, по которой вы пойдете.
7 И пошли (те) пятеро, и пришли в  Лаиш,   и увидели, что тамошние люди  живут безопасно,   спокойно и беспечно по обычаям  сидонитян,   и в той земле нет правителя, который бы их обижал. А (живут) они  далеко от сидонитян   и  ни с кем дела не имеют.   8 И пришли к своим собратьям в Цоръа и Эштаоль, и сказали им их собратья: что вы (можете рассказать)? 9 И сказали: давайте пойдем на них (войной), потому что  мы видели их землю   – она очень хороша. Чего вы ждете? Не медлите, пойдем и захватим (эту) землю! 10 Пойдем на беспечный народ и на обширную землю, которую отдал Господь нам в руки – туда, где ни в чем  на свете   нет недостатка.
11 И двинулись оттуда, из семейства сынов Дана, из Цоръа и Эштаоля,  шестьсот человек,   препоясанных оружием. 12 И поднялись, и стали станом в  Кирьят-Йеариме   в (наделе) Йеуды, потому и называется то место  Махане Дан   до сегодняшнего дня, (а оно расположено) за Кирьят-Йеаримом. 13 И пошли оттуда в горы Эфрайима, и пришли к дому Михи. 14 А те пять человек, что ходили разведывать Лаишскую землю, сказали своим собратьям: знаете ли вы, что в этих домах есть эфод, терафим, истукан и литая статуя? А теперь подумайте, что делать. 15 И завернули туда, и пришли в дом к юноше-левиту, в дом к Михе, и поздоровались с ним. 16 А шестьсот человек из колена Дана, препоясанные оружием,  стояли у ворот.   17 И вошли пять разведчиков в дом, и взяли истукан, эфод, терафим и литую статую, а священник стоял у ворот и вместе с ним шестьсот человек из колена Дана, препоясанные оружием. 18 А они вошли в дом к Михе и взяли истукан, эфод, терафим и литую статую, и сказал им священник: что вы делаете? 19 И отвечали ему: тише,  помалкивай   и иди с нами. Будь у нас священником,  (станешь нам, как) отец.   Что лучше – быть священником  у одного человека   или  у (целого) израильского колена?   20 И  понравилось это священнику,   и взял он эфод, терафим и истукан, и присоединился к народу. 21 И поднялись, и пошли, а детей, скот и (повозки с) имуществом пропустили вперед. 22 Они (уже) ушли далеко от дома Михи, когда жители соседних домов, (жившие) рядом с Михой,  собрались   и догнали сынов Дана. 23 И позвали сынов Дана, а те обернулись и сказали Михе: чего тебе (надо), что ты с ними  увязался?   24 И отвечал: богов, которых я себе сделал, вы забрали, священника тоже, и уходите. Что же у меня (осталось)? А еще спрашиваете, чего мне (надо). 25 И сказали сыны Дана: Чтоб мы голоса твоего больше не слышали!  А то нападут на вас   (наши)  обозленные   люди, тебя прикончат и семью перебьют. 26 И пошли сыны Дана своей дорогой, и увидел Миха, что они сильнее его, и повернул, и возвратился домой. 27 Они взяли те (предметы), что изготовил Миха, и священника, что у него был, и напали на Лаиш, на спокойный и беспечный народ,  и вырезали его, а город сожгли.   28  И никто не пришел на помощь,   потому что Цидон далеко и ни с кем они не имели дела. А (город располагался) в долине возле  Бет-Рехова.   И отстроили город, и поселились в нем. 29 И дали городу название  Дан,   по имени предка их Дана, который родился у  Йисраэля,   но раньше город назывался Лаиш. 30 И сыны Дана  установили себе истукан,   а  Йеонатан,   потомок Гершона,  сына Менашше,   и его потомки, были священниками в колене Дана  вплоть до изгнания из страны.   31 И поставили себе истукан Михи, который он сделал, и (стоял он там) все время,  пока дом Божий находился в Шило."""

# second_kings_16_duplicate = """1 а семнадцатый год Пекаха, сына Ремальяу, над Йеудой воцарился Ахаз,   сын Йотама. 2 При воцарении Ахазу было двадцать лет, и он царствовал в Иерусалиме шестнадцать лет, но не делал угодного Господу, своему Богу, как предок его Давид. 3 И пошел он путем израильских царей, и сына своего  провел через огонь   – подобно той мерзости, которую делают народы, изгнанные Господом от израильтян. 4 Он приносил жертвы и воскурения на высотах, на холмах и под каждым зеленым деревом. 5 В то время арамейский царь Рецин и израильский царь Пеках, сын Ремальяу, пошли войной на Иерусалим,  осадили Ахаза,   но воевать с ним не смогли. 6 При этом арамейский царь Рецин вернул  арамейцам   Эйлат и изгнал  иудеев   из Эйлота, а эдомитяне пришли в Эйлат и владеют им до сего дня. 7  И послал Ахаз   посланников к Тиглат Пелесеру, царю Ассирии, и велел передать: Я раб твой и сын твой, приди избавь меня от арамейского царя и от израильского царя, которые пошли на меня войной. 8  И взял Ахаз серебро и золото,   что в доме Господнем и в сокровищнице царского дворца, и послал ассирийскому царю как подношение. 9 И ассирийский царь исполнил его волю, и пошел ассирийский царь на Дамаск, и захватил его, и жителей изгнал в Кир, а Рецина убил. 10  И пошел царь Ахаз   на встречу ассирийскому царю Тиглат Пилесеру в Дамаск,  и увидел жертвенник,   что в Дамаске, и послал Урии-священнику изображение и чертеж жертвенника во всех подробностях. 11 И Урия-священник (еще) до возвращения царя Ахаза из Дамаска выстроил в точности (такой же) жертвенник (по чертежу), который прислал царь Ахаз из Дамаска. 12 И вернулся царь из Дамаска, и увидел царь жертвенник,  и принес царь на жертвеннике жертвы,   и поднялся на него. 13 И воскурил жертву всесожжения и приношение, и принес возлияние, и побрызгал жертвенник кровью своей пиршественной жертвы. 14  А бронзовый жертвенник, что перед Господом,   он передвинул от передней части Храма, (где он стоял) между (новым) жертвенником и домом Господним, и поставил его у северной стороны (нового) жертвенника. 15 И велел царь Ахаз Урии-священнику:  На большом жертвеннике приноси утреннюю жертву всесожжения и вечернее подношение,   царскую жертву всесожжения и подношение, жертвы всесожжения, подношения и возлияния народа, и кропи его кровью всех жертв всесожжения и пиршественных жертв, а бронзовый жертвенник останется мне  для созерцания.   16 И Урия-священник сделал все, как велел царь Ахаз. 17 И царь Ахаз  убрал обрамление с подставок,   а  умывальник и море снял   с бронзовых быков, которые их (поддерживали), и поставил на каменный помост. 18 А  субботний навес,   построенный в Храме, и внешний царский вход он убрал из Храма Господня из-за ассирийского царя. 19 А остальные дела Ахаза, которые он совершил, записаны в Книге летописи царей Йеуды. 20 И почил Ахаз с предками, и был похоронен с предками в Городе Давида, и на его месте воцарился его сын  Хизкийау.  """
second_kings_16_duplicate = """1 На семнадцатый год Пекаха, сына Ремальяу, над Йеудой воцарился Ахаз,   сын Йотама. 2 При воцарении Ахазу было двадцать лет, и он царствовал в Иерусалиме шестнадцать лет, но не делал угодного Господу, своему Богу, как предок его Давид. 3 И пошел он путем израильских царей, и сына своего  провел через огонь   – подобно той мерзости, которую делают народы, изгнанные Господом от израильтян. 4 Он приносил жертвы и воскурения на высотах, на холмах и под каждым зеленым деревом. 5 В то время арамейский царь Рецин и израильский царь Пеках, сын Ремальяу, пошли войной на Иерусалим,  осадили Ахаза,   но воевать с ним не смогли. 6 При этом арамейский царь Рецин вернул  арамейцам   Эйлат и изгнал  иудеев   из Эйлота, а эдомитяне пришли в Эйлат и владеют им до сего дня. 7  И послал Ахаз   посланников к Тиглат Пелесеру, царю Ассирии, и велел передать: Я раб твой и сын твой, приди избавь меня от арамейского царя и от израильского царя, которые пошли на меня войной. 8  И взял Ахаз серебро и золото,   что в доме Господнем и в сокровищнице царского дворца, и послал ассирийскому царю как подношение. 9 И ассирийский царь исполнил его волю, и пошел ассирийский царь на Дамаск, и захватил его, и жителей изгнал в Кир, а Рецина убил. 10  И пошел царь Ахаз   на встречу ассирийскому царю Тиглат Пилесеру в Дамаск,  и увидел жертвенник,   что в Дамаске, и послал Урии-священнику изображение и чертеж жертвенника во всех подробностях. 11 И Урия-священник (еще) до возвращения царя Ахаза из Дамаска выстроил в точности (такой же) жертвенник (по чертежу), который прислал царь Ахаз из Дамаска. 12 И вернулся царь из Дамаска, и увидел царь жертвенник,  и принес царь на жертвеннике жертвы,   и поднялся на него. 13 И воскурил жертву всесожжения и приношение, и принес возлияние, и побрызгал жертвенник кровью своей пиршественной жертвы. 14  А бронзовый жертвенник, что перед Господом,   он передвинул от передней части Храма, (где он стоял) между (новым) жертвенником и домом Господним, и поставил его у северной стороны (нового) жертвенника. 15 И велел царь Ахаз Урии-священнику:  На большом жертвеннике приноси утреннюю жертву всесожжения и вечернее подношение,   царскую жертву всесожжения и подношение, жертвы всесожжения, подношения и возлияния народа, и кропи его кровью всех жертв всесожжения и пиршественных жертв, а бронзовый жертвенник останется мне  для созерцания.   16 И Урия-священник сделал все, как велел царь Ахаз. 17 И царь Ахаз  убрал обрамление с подставок,   а  умывальник и море снял   с бронзовых быков, которые их (поддерживали), и поставил на каменный помост. 18 А  субботний навес,   построенный в Храме, и внешний царский вход он убрал из Храма Господня из-за ассирийского царя. 19 А остальные дела Ахаза, которые он совершил, записаны в Книге летописи царей Йеуды. 20 И почил Ахаз с предками, и был похоронен с предками в Городе Давида, и на его месте воцарился его сын  Хизкийау."""
# second_kings_17_duplicate = """1 а двенадцатый год Ахаза, царя Йеуды, в Шомроне воцарился  Ошеа,   сын Элы, и (правил) Израилем девять лет. 2 Он творил неугодное Господу,  но не так, как израильские цари,   что были до него. 3 На него пошел войной ассирийский царь  Шалманесер;   Ошеа стал его слугой и платил ему дань. 4 Но ассирийский царь заметил в нем неверность – Ошеа направил посланников к египетскому царю  Со,   а дань ассирийскому царю платил не каждый год. И схватил его ассирийский царь, и заключил в тюрьму. 5 И пошел ассирийский царь войной на всю страну,  осадил Шомрон  и  держал осаду три года.   6 На девятый год (правления) Ошеа царь Ассирии захватил Шомрон,  изгнал израильтян в Ассирию   и поселил их в  Хлахе,   в Хаворе, на реке  Гозан   и в городах  Мидии.
#  
#
#  
# 7  Ведь израильтяне согрешили перед Господом,   Богом своим, который вывел их из земли Египетской, из под власти фараона, царя египетского, и начали почитать других богов. 8 И стали жить по законам народов, которых Господь прогнал от израильтян, и (по законам) царей, которых они  назначили. 9 И израильтяне творили вещи, которые не нравились Господу, их Богу, и строили себе (святилища на) возвышенностях во всех своих городах – от сторожевых башен до крепостей. 10 И ставили памятники и кумирные деревья на всех высоких холмах и под всеми зелеными деревьями. 11 И совершали там воскурения на всех высотах, подобно народам, которые Господь изгнал от них, и делали нехорошие вещи, гневя Господа. 12 И служили истуканам, хоть и сказал им Господь: не делайте этого. 13 И предупреждал Господь Израиль и Йеуду устами всех своих пророков и провидцев: Сойдите с дурного пути и соблюдайте мои заповеди и законы – все наставления, которые я дал вашим предкам и послал вам через рабов своих, пророков. 14 Но они не слушали и упорствовали,  подобно своим предкам,   которые не верили Господу, Богу своему. 15 И они пренебрегали его законами и его заветом, который он заключил с их предками, и обязательствами, которые он им заповедал, и пошли за пустотой, и занялись пустыми делами, и (шли) за народами, их окружающими – то, что Господь запретил им делать. 16 И оставили все заповеди Господа, Бога своего, и сделали  себе изваяние – двух тельцов,   и сделали ашеру, и  поклонялись всему воинству небесному,   и служили Баалю. 17 И  проводили своих сыновей и дочерей   через огонь, и занимались колдовством и гаданием, и пристрастились делать неугодное Господу и гневить его. 18 И весьма разгневался Господь на Израиль, и прогнал его от себя, и  осталось только колено Йеуды.   19 Но (колено) Йеуды тоже не соблюдало  заповедей   Господа, Бога своего, а следовало законам Израиля, которые тот (себе) установил. 20 И опротивело Господу все семя Израиля, и он притеснял их и отдавал в руки мучителей, пока не прогнал их. 21 Ибо оторвал он Израиль от дома Давида и возвел на царство Йаровеама, сына Невата, а Йаровеам увлек Израиль прочь от Господа и ввел в великий грех. 22 И следовали израильтяне за всеми грехами Йаровеама, не отступаясь от них, 23 покуда Господь не прогнал от себя Израиль, как он говорил устами всех рабов своих, пророков, и был Израиль изгнан со своей земли в Ассирию  до сего дня.
#  
#
#  
# 24  И вывел ассирийский царь   (людей) из Вавилона, Куты, Авы, Хамата и Сефарвайима, и переселил их в города Шомрона вместо израильтян, и они заняли Шомрон и поселились в тамошних городах. 25 Когда они начали там жить, то не почитали Господа, и  Господь наслал на них львов,   которые их убивали. 26 И донесли ассирийскому царю: Народы, которые ты переселил в города Шомрона, не знают законов местного божества, которое наслало на них львов, и (эти львы) убивают их, потому что они не знают законов местного божества. 27  И велел ассирийский царь:   Отправьте туда одного из священников, которых вы оттуда выселили – пусть идет, селится там и учит их законам местного божества. 28 И пошел один из священников, переселенных из Шомрона, и поселился в Бет-Эле, и учил их, как  почитать Господа.   29 А каждый народ делал своих божков и устанавливал в святилищах на высотах, построенных жителями Шомрона – каждый народ в своем городе, где он жил. 30 Выходцы из Вавилона изваяли  Суккот-Бенота,   а жители Кута изваяли Нергала, а жители Хамата изваяли  Ашиму,   31 а выходцы из Авы изваяли  Нивхаза   и Тартака, а выходцы из Сефарвайима сжигали своих детей в огне во имя  Адраммелеха и Анаммелеха,   богов Сефарвайима. 32 Теперь же они стали почитать Господа и выбрали из своей среды священников на высоты, которые служили в святилищах на высотах. 33 Они  почитали Господа и (одновременно) служили своим богам по законам народов, из чьих (земель) их выселили. 34  До сегодняшнего дня они поступают   по своим прежним обычаям –  не почитают  Господа (как следует)   и не исполняют законов, правил, наставлений и заповедей, данных Господом сынам  Йаакова, чье имя он поменял на Йисраэль,   35 и заключил с ними завет и велел им: не почитайте других богов, не поклоняйтесь им, не служите им и не приносите им жертв, 36 но (поклоняйтесь) только Господу, который вывел вас из земли Египетской великой силой и простертой мышцей – его почитайте и ему поклоняйтесь и приносите жертвы, 37 а законы, правила, наставления и заповеди, написанные для вас, соблюдайте всю жизнь и не почитайте других богов, 38 и заключенный с вами завет не забывайте и других богов не почитайте, 39 а почитайте только Господа, Бога своего, который спасает вас от всех врагов. 40 Но не послушались они и поступают по своим прежним обычаям. 41 Эти народы почитали Господа и служили своим истуканам.  Их сыновья и внуки делают то же,   что их предки, до сего дня."""

second_kings_17_duplicate = """1 На двенадцатый год Ахаза, царя Йеуды, в Шомроне воцарился  Ошеа,   сын Элы, и (правил) Израилем девять лет. 2 Он творил неугодное Господу,  но не так, как израильские цари,   что были до него. 3 На него пошел войной ассирийский царь  Шалманесер;   Ошеа стал его слугой и платил ему дань. 4 Но ассирийский царь заметил в нем неверность – Ошеа направил посланников к египетскому царю  Со,   а дань ассирийскому царю платил не каждый год. И схватил его ассирийский царь, и заключил в тюрьму. 5 И пошел ассирийский царь войной на всю страну,  осадил Шомрон  и  держал осаду три года.   6 На девятый год (правления) Ошеа царь Ассирии захватил Шомрон,  изгнал израильтян в Ассирию   и поселил их в  Хлахе,   в Хаворе, на реке  Гозан   и в городах  Мидии.  
 

 
7  Ведь израильтяне согрешили перед Господом,   Богом своим, который вывел их из земли Египетской, из под власти фараона, царя египетского, и начали почитать других богов. 8 И стали жить по законам народов, которых Господь прогнал от израильтян, и (по законам) царей, которых они  назначили. 9 И израильтяне творили вещи, которые не нравились Господу, их Богу, и строили себе (святилища на) возвышенностях во всех своих городах – от сторожевых башен до крепостей. 10 И ставили памятники и кумирные деревья на всех высоких холмах и под всеми зелеными деревьями. 11 И совершали там воскурения на всех высотах, подобно народам, которые Господь изгнал от них, и делали нехорошие вещи, гневя Господа. 12 И служили истуканам, хоть и сказал им Господь: не делайте этого. 13 И предупреждал Господь Израиль и Йеуду устами всех своих пророков и провидцев: Сойдите с дурного пути и соблюдайте мои заповеди и законы – все наставления, которые я дал вашим предкам и послал вам через рабов своих, пророков. 14 Но они не слушали и упорствовали,  подобно своим предкам,   которые не верили Господу, Богу своему. 15 И они пренебрегали его законами и его заветом, который он заключил с их предками, и обязательствами, которые он им заповедал, и пошли за пустотой, и занялись пустыми делами, и (шли) за народами, их окружающими – то, что Господь запретил им делать. 16 И оставили все заповеди Господа, Бога своего, и сделали  себе изваяние – двух тельцов,   и сделали ашеру, и  поклонялись всему воинству небесному,   и служили Баалю. 17 И  проводили своих сыновей и дочерей   через огонь, и занимались колдовством и гаданием, и пристрастились делать неугодное Господу и гневить его. 18 И весьма разгневался Господь на Израиль, и прогнал его от себя, и  осталось только колено Йеуды.   19 Но (колено) Йеуды тоже не соблюдало  заповедей   Господа, Бога своего, а следовало законам Израиля, которые тот (себе) установил. 20 И опротивело Господу все семя Израиля, и он притеснял их и отдавал в руки мучителей, пока не прогнал их. 21 Ибо оторвал он Израиль от дома Давида и возвел на царство Йаровеама, сына Невата, а Йаровеам увлек Израиль прочь от Господа и ввел в великий грех. 22 И следовали израильтяне за всеми грехами Йаровеама, не отступаясь от них, 23 покуда Господь не прогнал от себя Израиль, как он говорил устами всех рабов своих, пророков, и был Израиль изгнан со своей земли в Ассирию  до сего дня.  
 

 
24  И вывел ассирийский царь   (людей) из Вавилона, Куты, Авы, Хамата и Сефарвайима, и переселил их в города Шомрона вместо израильтян, и они заняли Шомрон и поселились в тамошних городах. 25 Когда они начали там жить, то не почитали Господа, и  Господь наслал на них львов,   которые их убивали. 26 И донесли ассирийскому царю: Народы, которые ты переселил в города Шомрона, не знают законов местного божества, которое наслало на них львов, и (эти львы) убивают их, потому что они не знают законов местного божества. 27  И велел ассирийский царь:   Отправьте туда одного из священников, которых вы оттуда выселили – пусть идет, селится там и учит их законам местного божества. 28 И пошел один из священников, переселенных из Шомрона, и поселился в Бет-Эле, и учил их, как  почитать Господа.   29 А каждый народ делал своих божков и устанавливал в святилищах на высотах, построенных жителями Шомрона – каждый народ в своем городе, где он жил. 30 Выходцы из Вавилона изваяли  Суккот-Бенота,   а жители Кута изваяли Нергала, а жители Хамата изваяли  Ашиму,   31 а выходцы из Авы изваяли  Нивхаза   и Тартака, а выходцы из Сефарвайима сжигали своих детей в огне во имя  Адраммелеха и Анаммелеха,   богов Сефарвайима. 32 Теперь же они стали почитать Господа и выбрали из своей среды священников на высоты, которые служили в святилищах на высотах. 33 Они  почитали Господа и (одновременно) служили своим богам по законам народов, из чьих (земель) их выселили. 34  До сегодняшнего дня они поступают   по своим прежним обычаям –  не почитают  Господа (как следует)   и не исполняют законов, правил, наставлений и заповедей, данных Господом сынам  Йаакова, чье имя он поменял на Йисраэль,   35 и заключил с ними завет и велел им: не почитайте других богов, не поклоняйтесь им, не служите им и не приносите им жертв, 36 но (поклоняйтесь) только Господу, который вывел вас из земли Египетской великой силой и простертой мышцей – его почитайте и ему поклоняйтесь и приносите жертвы, 37 а законы, правила, наставления и заповеди, написанные для вас, соблюдайте всю жизнь и не почитайте других богов, 38 и заключенный с вами завет не забывайте и других богов не почитайте, 39 а почитайте только Господа, Бога своего, который спасает вас от всех врагов. 40 Но не послушались они и поступают по своим прежним обычаям. 41 Эти народы почитали Господа и служили своим истуканам.  Их сыновья и внуки делают то же,   что их предки, до сего дня."""
def scrape_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        source_html = str(soup)
        return (source_html)
    else:
        print(f"Failed to fetch URL. Status code: {response.status_code}")
def clean_soup(soup):
    remove_elements_by_tag(soup, "h3")
    remove_elements_by_tag(soup, "h4")
    remove_elements_by_class(soup, "additional-comment-container__content")
    # remove_elements_by_class(soup, "content-event-first")

def remove_elements_by_tag(soup, tag_name):
    elements_to_remove = soup.find_all(tag_name)
    for element in elements_to_remove:
        element.decompose()

def remove_elements_by_class(soup, class_name):
    elements_to_remove = soup.find_all(class_=class_name)
    for element in elements_to_remove:
        element.decompose()


def scrape_and_clean_chapter_content(url):
    html = scrape_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    clean_soup(soup)

    chapter_content_elements = soup.find_all(lambda tag: tag.has_attr('id') and tag['id'].startswith('chapter-content'))

    text_content = ''
    for element in chapter_content_elements:
        text_content += element.get_text()

    return text_content
parashot_urls = {"Genesis":
    [
        "https://dadada.live/books/chapter/bereshit-bereshit",
        "https://dadada.live/books/chapter/bereshit-noah",
        "https://dadada.live/books/chapter/bereshit-leh-leha",
        "https://dadada.live/books/chapter/bereshit-vaera",
        "https://dadada.live/books/chapter/bereshit-haei-sara",
        "https://dadada.live/books/chapter/bereshit-toldot",
        "https://dadada.live/books/chapter/bereshit-vaetze",
        "https://dadada.live/books/chapter/bereshit-vaishlah",
        "https://dadada.live/books/chapter/bereshit-vaeshev",
        "https://dadada.live/books/chapter/bereshit-miketz",
        "https://dadada.live/books/chapter/bereshit-vaigash",
        "https://dadada.live/books/chapter/bereshit-vaehi"

    ],
    "Exodus":[
        "https://dadada.live/books/chapter/shmot-shmot",
        "https://dadada.live/books/chapter/shmot-vaera",
        "https://dadada.live/books/chapter/shmot-bo",
        "https://dadada.live/books/chapter/shmot-beshalah",
        "https://dadada.live/books/chapter/shmot-itro",
        "https://dadada.live/books/chapter/shmot-mishpatim",
        "https://dadada.live/books/chapter/shmot-truma",
        "https://dadada.live/books/chapter/shmot-tetzave",
        "https://dadada.live/books/chapter/shmot-tisa",
        "https://dadada.live/books/chapter/shmot-vayakhel",
        "https://dadada.live/books/chapter/shmot-pkudei",
    ],
    "Leviticus":[
        "https://dadada.live/books/chapter/vaikra-vaikra",
        "https://dadada.live/books/chapter/vaikra-tzav",
        "https://dadada.live/books/chapter/vaikra-shmini",
        "https://dadada.live/books/chapter/vaikra-tazriya",
        "https://dadada.live/books/chapter/vaikra-metzora",
        "https://dadada.live/books/chapter/vaikra-aharei-mot",
        "https://dadada.live/books/chapter/vaikra-kdoshim",
        "https://dadada.live/books/chapter/vaikra-emor",
        "https://dadada.live/books/chapter/vaikra-behar",
        "https://dadada.live/books/chapter/vaikra-behukotai",
    ],
    "Numbers":[
        "https://dadada.live/books/chapter/bemidbar-bemidbar",
        "https://dadada.live/books/chapter/bemidbar-naso",
        "https://dadada.live/books/chapter/bemidbar-behaalotha",
        "https://dadada.live/books/chapter/bemidbar-shlah",
        "https://dadada.live/books/chapter/bemidbar-korah",
        "https://dadada.live/books/chapter/bemidbar-hukat",
        "https://dadada.live/books/chapter/bemidbar-balak",
        "https://dadada.live/books/chapter/bemidbar-pinhas",
        "https://dadada.live/books/chapter/bemidbar-matot",
        "https://dadada.live/books/chapter/bemidbar-maseei",
        ],
    "Deuteronomy":[
        "https://dadada.live/books/chapter/dvarim-dvarim",
        "https://dadada.live/books/chapter/dvarim-vaethanan",
        "https://dadada.live/books/chapter/dvarim-ekev",
        "https://dadada.live/books/chapter/dvarim-re",
        "https://dadada.live/books/chapter/dvarim-shoftim",
        "https://dadada.live/books/chapter/dvarim-ki-tece",
        "https://dadada.live/books/chapter/dvarim-ki-tavo",
        "https://dadada.live/books/chapter/dvarim-nicavim",
        "https://dadada.live/books/chapter/dvarim-vaeleh",
        "https://dadada.live/books/chapter/dvarim-haazinu",
        "https://dadada.live/books/chapter/dvarim-ve-zot-ha-braha"
    ],
    "Judges": [
        # "https://dadada.live/books/chapter/sudi-prodolzenie-zavoevaniya",
        # "https://dadada.live/books/chapter/sudi-osobennosti-epoxi-sudei",
        # "https://dadada.live/books/chapter/sudi-otniel-eud-samgar",
        # "https://dadada.live/books/chapter/sudi-voina-s-siseroi",
        # "https://dadada.live/books/chapter/sudi-pesn-devory",
        # "https://dadada.live/books/chapter/sudi-nacalo-puti-gideona",
        # "https://dadada.live/books/chapter/sudi-voina-gideona-s-midyanom",
        # "https://dadada.live/books/chapter/sudi-prodolzenie-pravleniya-gideona",
        # "https://dadada.live/books/chapter/sudi-avimelex",
        # "https://dadada.live/books/chapter/sudi-posle-avimelexa",
        # "https://dadada.live/books/chapter/sudi-iiftax",
        # "https://dadada.live/books/chapter/sudi-voina-iiftaxa-s-efraiimlyanami",
        # "https://dadada.live/books/chapter/sudi-rozdenie-simsona",
        # "https://dadada.live/books/chapter/sudi-zenitba-simsona",
        # "https://dadada.live/books/chapter/sudi-pobedy-simsona-nad-filistimlyanami",
        # "https://dadada.live/books/chapter/sudi-simson-i-delila",
        # "https://dadada.live/books/chapter/sudi-istukan-mixi-i-levit",
        # "https://dadada.live/books/chapter/sudi-syny-dana-i-istukan",
        # "https://dadada.live/books/chapter/sudi-naloznica-v-give",
        # "https://dadada.live/books/chapter/sudi-voina-s-kolenom-binyamina",
        # "https://dadada.live/books/chapter/sudi-vosstanovlenie-kolena-binyamina"

        "https://dadada.live/books/chapter/shoftim-1",
        "https://dadada.live/books/chapter/shoftim-2",
        "https://dadada.live/books/chapter/shoftim-3",
        "https://dadada.live/books/chapter/shoftim-4",
        "https://dadada.live/books/chapter/shoftim-5",
        "https://dadada.live/books/chapter/shoftim-6",
        "https://dadada.live/books/chapter/shoftim-7",
        "https://dadada.live/books/chapter/shoftim-8",
        "https://dadada.live/books/chapter/shoftim-9",
        "https://dadada.live/books/chapter/shoftim-10",
        "https://dadada.live/books/chapter/shoftim-11",
        "https://dadada.live/books/chapter/shoftim-12",
        "https://dadada.live/books/chapter/shoftim-13",
        "https://dadada.live/books/chapter/shoftim-14",
        "https://dadada.live/books/chapter/shoftim-15",
        "https://dadada.live/books/chapter/shoftim-16",
        "https://dadada.live/books/chapter/shoftim-17",
        "https://dadada.live/books/chapter/shoftim-18",
        "https://dadada.live/books/chapter/shoftim-19",
        "https://dadada.live/books/chapter/shoftim-20",
        "https://dadada.live/books/chapter/shoftim-21"

    ],
    "I_Samuel": [
        "https://dadada.live/books/chapter/smuel-i-rozdenie-semuelya",
        "https://dadada.live/books/chapter/smuel-i-proklyatie-roda-eli",
        "https://dadada.live/books/chapter/smuel-i-semuel-stanovitsya-prorokom",
        "https://dadada.live/books/chapter/smuel-i-voina-s-filistimlyanami",
        "https://dadada.live/books/chapter/smuel-i-kovceg-u-filistimlyan",
        "https://dadada.live/books/chapter/smuel-i-vozvrashhenie-kovcega",
        "https://dadada.live/books/chapter/smuel-i-pobeda-semuelya-nad-filistimlyanami",
        "https://dadada.live/books/chapter/smuel-i-prosba-o-care",
        "https://dadada.live/books/chapter/smuel-i-prixod-saulya",
        "https://dadada.live/books/chapter/smuel-i-pomazanie-saulya",
        "https://dadada.live/books/chapter/smuel-i-voina-s-ammonityanami",
        "https://dadada.live/books/chapter/smuel-i-rec-semuelya",
        "https://dadada.live/books/chapter/smuel-i-pered-boem-s-filistimlyanami",
        "https://dadada.live/books/chapter/smuel-i-pobeda-nad-filistimlyanami-314",
        "https://dadada.live/books/chapter/smuel-i-voina-s-amalekityanami",
        "https://dadada.live/books/chapter/smuel-i-pomazanie-davida",
        "https://dadada.live/books/chapter/smuel-i-david-i-golyat",
        "https://dadada.live/books/chapter/smuel-i-vrazdebnost-saulya-k-davidu",
        "https://dadada.live/books/chapter/smuel-i-begstvo-davida",
        "https://dadada.live/books/chapter/smuel-i-david-i-ionatan",
        "https://dadada.live/books/chapter/smuel-i-david-v-nove",
        "https://dadada.live/books/chapter/smuel-i-istreblenie-zitelei-nova",
        "https://dadada.live/books/chapter/smuel-i-spasenie-keily",
        "https://dadada.live/books/chapter/smuel-i-david-i-saul-v-peshhere",
        "https://dadada.live/books/chapter/smuel-i-naval-i-avigail",
        "https://dadada.live/books/chapter/smuel-i-david-v-stane-saulya",
        "https://dadada.live/books/chapter/smuel-i-david-u-filistimlyan",
        "https://dadada.live/books/chapter/smuel-i-saul-i-vorozeya-v-en-dore",
        "https://dadada.live/books/chapter/smuel-i-vozvrashhenie-davida",
        "https://dadada.live/books/chapter/smuel-i-pobeda-davida-nad-amalekityanami",
        "https://dadada.live/books/chapter/smuel-i-smert-saulya",
    ],
    "II_Samuel": [
        "https://dadada.live/books/chapter/smuel-ii-posle-gibeli-saulya-314",
        "https://dadada.live/books/chapter/smuel-ii-dva-carya",
        "https://dadada.live/books/chapter/smuel-ii-ubiistvo-avnera",
        "https://dadada.live/books/chapter/smuel-ii-ubiistvo-is-boseta",
        "https://dadada.live/books/chapter/smuel-ii-david-car-nad-izrailem",
        "https://dadada.live/books/chapter/smuel-ii-perenos-kovcega",
        "https://dadada.live/books/chapter/smuel-ii-soyuz-s-davidom",
        "https://dadada.live/books/chapter/smuel-ii-voiny-davida",
        "https://dadada.live/books/chapter/smuel-ii-david-i-mefivoset",
        "https://dadada.live/books/chapter/smuel-ii-voina-s-ammonityanami",
        "https://dadada.live/books/chapter/smuel-ii-david-i-bat-seva",
        "https://dadada.live/books/chapter/smuel-ii-oblicenie-natana",
        "https://dadada.live/books/chapter/smuel-ii-amnon-i-tamar",
        "https://dadada.live/books/chapter/smuel-ii-mudraya-zenshhina-iz-tekoa",
        "https://dadada.live/books/chapter/smuel-ii-zagovor-avsaloma",
        "https://dadada.live/books/chapter/smuel-ii-david-v-puti",
        "https://dadada.live/books/chapter/smuel-ii-sovet-axitofelya",
        "https://dadada.live/books/chapter/smuel-ii-gibel-avsaloma",
        "https://dadada.live/books/chapter/smuel-ii-vozvrashhenie-davida-na-carstvo",
        "https://dadada.live/books/chapter/smuel-ii-bunt-sevy-syna-bixri",
        "https://dadada.live/books/chapter/smuel-ii-vydaca-potomkov-saulya",
        "https://dadada.live/books/chapter/smuel-ii-pesn-davida",
        "https://dadada.live/books/chapter/smuel-ii-voiny-davida-314",
        "https://dadada.live/books/chapter/smuel-ii-podscet-naroda",
    ],
    "I_Kings": [
        "https://dadada.live/books/chapter/mlaxim-i-pomazanie-selomo",
        "https://dadada.live/books/chapter/mlaxim-i-vocarenie-selomo",
        "https://dadada.live/books/chapter/mlaxim-i-mudrost-selomo",
        "https://dadada.live/books/chapter/mlaxim-i-namestniki-selomo",
        "https://dadada.live/books/chapter/mlaxim-i-blagopolucie-carstva-selomo",
        "https://dadada.live/books/chapter/mlaxim-i-stroitelstvo-doma-dlya-gospoda",
        "https://dadada.live/books/chapter/mlaxim-i-raboty-xirama-dlya-doma-gospodnya",
        "https://dadada.live/books/chapter/mlaxim-i-osvyashhenie-doma-gospodnya",
        "https://dadada.live/books/chapter/mlaxim-i-velicie-selomo",
        "https://dadada.live/books/chapter/mlaxim-i-vizit-caricy-savskoi",
        "https://dadada.live/books/chapter/mlaxim-i-zaversenie-carstvovaniya-selomo",
        "https://dadada.live/books/chapter/mlaxim-i-razdelenie-carstva",
        "https://dadada.live/books/chapter/mlaxim-i-celovek-bozii-v-bet-ele",
        "https://dadada.live/books/chapter/mlaxim-i-iaroveam-i-rexaveam",
        "https://dadada.live/books/chapter/mlaxim-i-aviiam-asa-nadav-i-baasa",
        "https://dadada.live/books/chapter/mlaxim-i-baasa-ela-zimri-omri-axav",
        "https://dadada.live/books/chapter/mlaxim-i-eliiau-v-carefate",
        "https://dadada.live/books/chapter/mlaxim-i-eliiau-na-gore-karmel",
        "https://dadada.live/books/chapter/mlaxim-i-eliiau-v-xoreve",
        "https://dadada.live/books/chapter/mlaxim-i-voina-s-ben-adadom",
        "https://dadada.live/books/chapter/mlaxim-i-vinogradnik-navota",
        "https://dadada.live/books/chapter/mlaxim-i-axav-i-ieosafat"
    ],
    "II_Kings":[
        "https://dadada.live/books/chapter/mlaxim-ii-axazyau-i-eliiau",
        "https://dadada.live/books/chapter/mlaxim-ii-eliiau-i-elisa",
        "https://dadada.live/books/chapter/mlaxim-ii-voina-s-moavom",
        "https://dadada.live/books/chapter/mlaxim-ii-cudesa-elisy",
        "https://dadada.live/books/chapter/mlaxim-ii-elisa-i-naaman",
        "https://dadada.live/books/chapter/mlaxim-ii-elisa-i-arameicy",
        "https://dadada.live/books/chapter/mlaxim-ii-stan-arameicev",
        "https://dadada.live/books/chapter/mlaxim-ii-deyatelnost-elisi",
        "https://dadada.live/books/chapter/mlaxim-ii-zagovor-ieu",
        "https://dadada.live/books/chapter/mlaxim-ii-ieu-v-somrone",
        "https://dadada.live/books/chapter/mlaxim-ii-atalya",
        "https://dadada.live/books/chapter/mlaxim-ii-ieoas",
        "https://dadada.live/books/chapter/mlaxim-ii-ieoaxaz-i-ieoas",
        "https://dadada.live/books/chapter/mlaxim-ii-amacyau-ieoas-i-iaroveam",
        "https://dadada.live/books/chapter/mlaxim-ii-azarya-iotam-i-cari-izrailya",
        "https://dadada.live/books/chapter/mlaxim-ii-axaz",
        "https://dadada.live/books/chapter/mlaxim-ii-izgnanie-izrailtyan",
        "https://dadada.live/books/chapter/mlaxim-ii-xizkiya",
        "https://dadada.live/books/chapter/mlaxim-ii-osada-ierusalima",
        "https://dadada.live/books/chapter/mlaxim-ii-okoncanie-carstvovaniya-xizkiiau",
        "https://dadada.live/books/chapter/mlaxim-ii-menasse-i-amon",
        "https://dadada.live/books/chapter/mlaxim-ii-iosiiau",
        "https://dadada.live/books/chapter/mlaxim-ii-iosiiau-ieoaxaz-i-ieoiakim",
        "https://dadada.live/books/chapter/mlaxim-ii-ieoiakim-ieoiaxin-i-cidkiiau",
        "https://dadada.live/books/chapter/mlaxim-ii-razrusenie-ierusalima-i-xrama",
    ],
    "Ruth":
    [
        "https://dadada.live/books/chapter/rut-uxod-i-vozvrashhenie-naomi",
        "https://dadada.live/books/chapter/rut-rut-na-pole-boaza",
        "https://dadada.live/books/chapter/rut-rut-na-toke",
        "https://dadada.live/books/chapter/rut-semya-boaza-i-rut"
    ],
    "Esther":
        [
            "https://dadada.live/books/chapter/ester-pir-axasverosa",
            "https://dadada.live/books/chapter/ester-ester-stanovitsya-caricei",
            "https://dadada.live/books/chapter/ester-vozvysenie-amana",
            "https://dadada.live/books/chapter/ester-slova-mordexaya-i-ester",
            "https://dadada.live/books/chapter/ester-pervyi-pir",
            "https://dadada.live/books/chapter/ester-pocet-mordexayu",
            "https://dadada.live/books/chapter/ester-kazn-amana",
            "https://dadada.live/books/chapter/ester-ukaz-mordexaya",
            "https://dadada.live/books/chapter/ester-pobeda-i-prazdnovanie",
            "https://dadada.live/books/chapter/ester-velicie-mordexaya",

        ]

}

def ingest_version(book_map):
    book_name = next(iter(book_map)).split(" ")[0]
    book_name = book_name.replace("_", " ")
    index = library.get_index(book_name)
    cur_version = VersionSet({'title': book_name,
                              "versionTitle" : "Russian Torah translation, by Dmitri Slivniak, Ph.D., edited by Dr. Itzhak Streshinsky [ru]"})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "Russian Torah translation, by Dmitri Slivniak, Ph.D., edited by Dr. Itzhak Streshinsky [ru]",
                       "versionSource": "https://dadada.live/books",
                       "title": book_name,
                       "language": "en",
                       "chapter": chapter,
                       "digitizedBySefaria": True,
                       "license": "PD",
                       "status": "locked"
                       })
    modify_bulk_text(superuser_id, version, book_map)
def edge_cases_cleaner(text_content):
    text_content = text_content.replace("Народы, которые оставил Господь, судьи Отниэль, Эуд и Шамгар (3: 1-31)", '')
    text_content = text_content.replace(judges_18_duplicate, '', 1)
    text_content = text_content.replace("Авигаиль убеждает Давида не мстить Навалю (25: 1-44)", "")


    text_content = text_content.replace("Шеломо просит у Господа мудрости (3: 1-28)", "")
    text_content = text_content.replace("Дом Шеломо и работы, которые Хирам делал для дома Господня (7: 1-51)", '')
    text_content = text_content.replace("Вельможи и наместники Шеломо (4: 1-20)", "")
    text_content = text_content.replace("Богатство и мудрость Шеломо (5: 1-32)", "")
    text_content = text_content.replace("Шеломо строит дом для Господа (6: 1-38)", "")
    text_content = text_content.replace("6: 1-10", "")
    text_content = text_content.replace("7: 1-12", "")
    text_content = text_content.replace("Шеломо освящает дом Господень (8: 1-66)", "")
    text_content = text_content.replace("8: 1-11", "")
    text_content = text_content.replace("Величие Шеломо и его отношения с Хирамом (9: 1-28)", "")
    text_content = text_content.replace("9: 1-12","")
    text_content = text_content.replace("Царица Савская приходит в Иерусалим (10: 1-29)", "")
    text_content = text_content.replace("10: 1-13", "")
    text_content = text_content.replace("Шеломо творит неугодное Господу и последствия этого (11: 1-43)", "")
    text_content = text_content.replace("11: 1-10", "")
    # text_content = text_content.replace("Разделение царства между Рехавеамом и Йаровеамом  (12: 1-33)", "")
    text_content = text_content.replace("Разделение царства между Рехавеамом и Йаровеамом  (12: 1-33)", "")
    text_content = text_content.replace("12: 1-17", "")
    text_content = text_content.replace("Человек Божий из надела Йеуды приходит в Бет-Эль (13: 1-34)", "")
    text_content = text_content.replace("13: 1-10", "")
    text_content = text_content.replace("События царствований Йаровеама и Рехавеама (14: 1-31)", "")
    text_content = text_content.replace("14: 1-20", "")
    text_content = text_content.replace("Элийау живет у вдовы в Царефате (17: 1-24)", "")
    # text_content = text_content.replace("А  арамейский царь    Бен-Адад   собрал все свое войско,", "1 А  арамейский царь    Бен-Адад   собрал все свое войско,")
    text_content = text_content.replace("арамейский царь    Бен-Адад   собрал все свое войско,", "1 арамейский царь    Бен-Адад   собрал все свое войско,")
    text_content = text_content.replace("В это время   заболел  Авия,   сын Йаровеама.", "1 В это время   заболел  Авия,   сын Йаровеама.")

    text_content = text_content.replace("После смерти Ахава   моавитяне восстали против Израиля.", "1 После смерти Ахава   моавитяне восстали против Израиля.")
    text_content = text_content.replace("2 3 А остальные дела Йорама,", "23 А остальные дела Йорама,")
    text_content = text_content.replace(" был важным и уважаемым человеком у своего господина", "1 был важным и уважаемым человеком у своего господина")
    text_content = text_content.replace("А Элиша говорил   женщине, у которой он воскресил сына", "1 А Элиша говорил   женщине, у которой он воскресил сына")
    text_content = text_content.replace("Царствование Йеоаша (12: 1-22)", "")
    text_content = text_content.replace("12: 1-6", "")
    text_content = text_content.replace("Царствование Ахаза в Йеуде (16: 1-20)", "")
    text_content = text_content.replace(second_kings_16_duplicate, '', 1)
    text_content = text_content.replace(second_kings_17_duplicate, '', 1)
    text_content = text_content.replace("События окончательного этапа царствования Хизкийау (20: 1-21)", "")
    text_content = text_content.replace("20: 1-21", "")
    text_content = text_content.replace("Так и передали царю.Царствования Йошийау, Йеоахаза и Йеойакима (23: 1-37)", "")
    text_content = text_content.replace("23: 1-30", "")
    text_content = text_content.replace("Восемнадцатый год царствования Йошийау (22: 1-20)", "")

    text_content = text_content.replace("Уход Ноами из Бет-Лехема в Моав и ее возвращение (1: 1-22)", "")
    text_content = text_content.replace("Рут приходит в поле Боаза собирать колосья (2: 1-23)", "")
    text_content = text_content.replace("Рут приходит на ток Боаза (3: 1-18)", "")
    text_content = text_content.replace("Боаз женится на Рут (4: 1-22)","")

    text_content = text_content.replace("Ахашверош устраивает пир  (1: 1-22)", "")
    text_content = text_content.replace("Эстер взята в царский дом и царь полюбил ее (2: 1-23)", "")
    text_content = text_content.replace("Царь Ахашверош возвеличивает Амана (3: 1-15)", "")
    text_content = text_content.replace("Мордехай велит Эстер пойти к царю (4: 1-17)", "")
    text_content = text_content.replace("Первый пир царя и Амана с Эстер (5: 1-14)", "")
    text_content = text_content.replace("Ахашверош велит Аману оказать почет Мордехаю (6: 1-14)", "")
    text_content = text_content.replace("Пир во второй день и казнь Амана (7: 1-10)", "")
    text_content = text_content.replace("Мордехай пишет указ от имени Ахашвероша (8: 1-17)", "")
    text_content = text_content.replace("Победа иудеев и повеления отмечать праздник Пурим (9: 1-32)", "")
    text_content = text_content.replace("Мордехай второй после царя Ахашвероша      (10: 1-3)", "")

    text_content = text_content.replace("Элиша исцеляет Наамана (5: 1-27)", '')
    text_content = text_content.replace("5: 1-19", '')
    text_content = text_content.replace("1 был важным и уважаемым человеком у", " был важным и уважаемым человеком у")

    text_content = text_content.replace("Он убил своим [cm id='19625']копьем   триста человек[/cm]", "Он убил своим копьем   триста человек")


    return text_content
def handle_tanakh_book(book_name):
    text_content = ''
    for url in parashot_urls[book_name]:
        text_content += scrape_and_clean_chapter_content(url)
    text_content = edge_cases_cleaner(text_content)
    verse_nums_and_verses = re.split(r'(\d+)', text_content)
    # verse_nums_and_verses = [item.strip() for item in verse_nums_and_verses if item.strip()]
    verse_nums_and_verses = [item for item in verse_nums_and_verses if item != "" and not item.isspace()]
    verse_nums_and_verses = [item.strip() for item in verse_nums_and_verses]


    verse_nums_list = verse_nums_and_verses[::2]
    c = verse_nums_list.count('1')
    verses_list = verse_nums_and_verses[1::2]
    verses_list = [verse.replace("\n", "<br>") for verse in verses_list]
    verses_list = [verse.replace(" ", " ") for verse in verses_list]
    verses_list = [verse.replace("  ", " ") for verse in verses_list]
    trefs_list = []

    # Find duplicates using a set
    duplicates = set()
    unique_elements = set()

    for item in verses_list:
        if item in unique_elements:
            duplicates.add(item)
        else:
            unique_elements.add(item)

    # print("Duplicates in the list:", list(duplicates))

    perek = 0
    for verse_num in verse_nums_list:
        if verse_num == '1':
            perek += 1
        trefs_list.append(f"{book_name} {perek}:{verse_num}")

    book_map = dict(zip(trefs_list, verses_list))

    ingest_version(book_map)

def is_russian(sentence):
    # Regular expression to match Russian characters
    russian_pattern = re.compile('[а-яА-ЯёЁ]+')

    # Search for Russian characters in the sentence
    match = russian_pattern.search(sentence)

    # If there is a match, the sentence contains Russian characters
    return bool(match)
def get_prefix(input_string):
    index_of_colon = input_string.find(':')
    if index_of_colon != -1:
        return input_string[:index_of_colon]
    else:
        return input_string

def russian_version_stricter_validation():
    for book in parashot_urls.keys():
        segment_refs = library.get_index(book).all_segment_refs()
        for s_g in segment_refs:
            # en_version_text = s_g.text().text
            # ru_version_text = s_g.text(vtitle="Russian Torah translation, by Dmitri Slivniak, Ph.D., edited by Dr. Itzhak Streshinsky [ru]").text
            chapter_ref = Ref(get_prefix(s_g.tref))
            whole_chapter_en = chapter_ref.text().text
            whole_chapter_ru = chapter_ref.text(vtitle="Russian Torah translation, by Dmitri Slivniak, Ph.D., edited by Dr. Itzhak Streshinsky [ru]").text
            for en_verse, ru_verse in zip(whole_chapter_en, whole_chapter_ru):
                if en_verse == ru_verse:
                    print(chapter_ref)



def russian_version_validation():
    for book in parashot_urls.keys():
        segment_refs = library.get_index(book).all_segment_refs()
        for s_r in segment_refs:
            en_version_text = s_r.text().text
            ru_version_text = s_r.text(vtitle="Russian Torah translation, by Dmitri Slivniak, Ph.D., edited by Dr. Itzhak Streshinsky [ru]").text
            if s_r == Ref("Judges.5.32"):
                a = "halt"
            if en_version_text == '' or ru_version_text == '':
                print(f"problem in {s_r}")


if __name__ == '__main__':
    print("hello world")
    # handle_tanakh_book("Genesis")
    # handle_tanakh_book("Exodus")
    # handle_tanakh_book("Leviticus")
    # handle_tanakh_book("Numbers")
    # handle_tanakh_book("Deuteronomy")
    #
    # handle_tanakh_book("Judges")
    # handle_tanakh_book("I_Samuel")
    # handle_tanakh_book("II_Samuel")
    # handle_tanakh_book("I_Kings")
    # handle_tanakh_book("II_Kings")
    # handle_tanakh_book("Ruth")
    # handle_tanakh_book("Esther")
    ru_version_text = Ref("Judges.5").text(vtitle="Russian Torah translation, by Dmitri Slivniak, Ph.D., edited by Dr. Itzhak Streshinsky [ru]").text
    en_version_text = Ref("Judges.5").text().text
    russian_version_stricter_validation()


    print("end")



