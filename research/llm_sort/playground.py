import django
django.setup()

from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models import ChatOpenAI

# from tqdm import tqdm
from sefaria.model import *
from sefaria.helper.normalization import NormalizerComposer

from pprint import pprint


def get_normalizer():
    return NormalizerComposer(['unidecode', 'br-tag', 'itag', 'html', 'maqaf', 'cantillation', 'double-space'])


normalizer = get_normalizer()
def get_gpt_compare(system_prompt, human_prompt_generator, llm):
    content_to_val = {"1":-1, "2":1, "0":0}
    def gpt_compare(a, b) -> int:
        response = llm([system_prompt, human_prompt_generator(a, b)])
        print(a)
        print(b)
        print(response.content, content_to_val.get(response.content, 0))
        return content_to_val.get(response.content, 0)

    return gpt_compare


def sort_by_instruction(documents: list[str], comparison_instruction):
    from functools import cmp_to_key
    message_suffix = " The only output should be either '1' or '2' or '0'"
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    system = SystemMessage(
        content=
        comparison_instruction
        +message_suffix)
    human_generator = lambda a, b: HumanMessage(content=f"1) {a}\n2) {b}")
    documents.sort(key=cmp_to_key(get_gpt_compare(system, human_generator, llm)))
    # for document in documents:
    #     print(document)
    return documents


vine_jokes = ["“I’d like to start with the chimney jokes – I’ve got a stack of them. The first one is on the house.”", "“I did a gig in a fertility clinic. I got a standing ovulation.”", "“I had a dream last night that I was cutting carrots with the Grim Reaper – dicing with death.”", "“I rang up British Telecom and said: ‘I want to report a nuisance caller.’ He said: ‘Not you again.'”", "“I saw this bloke chatting-up a cheetah and I thought: ‘He’s trying to pull a fast one.'”", "“The advantages of easy origami are two-fold.”", "“I rang up my local swimming baths. I said: ‘Is that the local swimming baths?’ He said: ‘It depends where you’re calling from.'”", "“I said to the gym instructor: ‘Can you teach me to do the splits?’ He said: ‘How flexible are you?’ I said: ‘I can’t make Tuesdays.'”", "“I’m against hunting. In fact, I’m a hunt saboteur. I go out the night before and shoot the fox.”", "“This policeman came up to me with a pencil and a piece of very thin paper. He said, ‘I want you to trace someone for me.'”", "“I met this bloke with a didgeridoo and he was playing Dancing Queen on it. I thought, ‘that’s Abba-riginal.'”", "“I’ve decided to sell my Hoover – it was just collecting dust.”", "“I was getting into my car, and this bloke says to me ‘Can you give me a lift?’ I said ‘Sure, you look great, the world’s your oyster, go for it.'”", "“I went down the local supermarket. I said: ‘I want to make a complaint – this vinegar’s got lumps in it.’ He said: ‘Those are pickled onions.'”", "“I’ll tell you what I love doing more than anything – trying to pack myself in a small suitcase. I can hardly contain myself.”", "“I was at sea the other day and loads of meat floated past. It was a bit choppy.”", "“You know, somebody actually complimented me on my driving today. They left a little note on the windscreen, it said ‘Parking Fine.’ So that was nice.”", "“I’m so lazy I’ve got a smoke alarm with a snooze button.”", "“I’ve spent the afternoon re-arranging the furniture in Dracula’s house. I was doing a bit of Fang-Shui.”", "“I was stealing things in the supermarket today while balanced on the shoulders of vampires. I was charged with shoplifting on three counts.”", "“Uncle Ben has died. No more Mr Rice Guy.”", "“I once did a gig in a zoo. I got babooned off.”", "“Eric Bristow asked me why I put superglue on one of his darts. I said ‘you just can’t let it go can you?'”", "“I saw this advert in a window that said: ‘Television for sale, £1, volume stuck on full.’ I thought, ‘I can’t turn that down.'”", "“I’ve just been on a once-in-a-lifetime holiday. I’ll tell you what, never again.”", "“Do you ever get that when you’re half way through eating a horse and you think to yourself, ‘I’m not as hungry as I thought I was?'”", "“Black Beauty – now there’s a dark horse.”", "Tim Vine has won numerous best joke awards (Photo: Getty)", "“I was reading a book – ‘The History of Glue’ – I couldn’t put it down.”", "“I got home, and the phone was ringing. I picked it up, and said ‘Who’s speaking please?’ And a voice said ‘You are.'”", "“Exit signs? They’re on the way out!”", "“Velcro? What a rip-off!”", "“I went to buy a watch, and the man in the shop said ‘Analogue?’ I said ‘No, just a watch.'”", "“I was in this restaurant and I asked for something herby. They gave me a Volkswagen with no driver.”", "“I went to the doctor. I said to him ‘I’m frightened of lapels.’ He said, ‘You’ve got cholera.'”", "“I met the bloke who invented crosswords today. I can’t remember his name, it’s P-something T-something R…”", "“I was having dinner with my boss and his wife said, ‘How many potatoes would you like, Tim?’. I said ‘Ooh, I’ll just have one please.’ She said ‘It’s OK, you don’t have to be polite.’ ‘Alright,’ I said, ‘I’ll just have one then, you stupid cow.’", "“A friend of mine always wanted to be run over by a steam train. When it happened, he was chuffed to bits!”", "“I was in the army once and the Sergeant said to me: ‘What does surrender mean?’ I said: ‘I give up!'”", "“This bloke said to me: ‘I’m going to attack you with the neck of a guitar.’ I said: ‘Is that a fret?'”", "“I saw Arnold Schwarzenegger eating a chocolate egg. I said: ‘I bet I know what your favourite Christian festival is.’ He said: ‘You have to love Easter, baby.'”", "“I used go out with an anaesthetist – she was a local girl.”", "“Crime in multi-storey car parks. That is wrong on so many different levels.”", "“I went to a Pretenders concert. It was a tribute act.”", "“I went down my local ice-cream shop, and said ‘I want to buy an ice-cream’. He said ‘Hundreds & thousands?’ I said ‘We’ll start with one.’ He said ‘Knickerbocker glory?’ I said ‘I do get a certain amount of freedom in these trousers, yes.'”", "“I bought a train ticket and the driver said ‘Eurostar?’ I said ‘Well, I’ve been on telly but I’m no Dean Martin.’ Still, at least it’s comfortable on Eurostar – it’s murder on the Orient Express.”", "“I went into a shop and I said, ‘Can someone sell me a kettle?’ The bloke said ‘Kenwood?’ I said, ‘Where is he?'”", "“I went in to a pet shop. I said, ‘Can I buy a goldfish?’ The guy said, ‘Do you want an aquarium?’ I said, ‘I don’t care what star sign it is.'”", "“You know, I’m not very good at magic – I can only do half of a trick. I’m a member of the Magic Semi-circle.”", "“My next door neighbour worships exhaust pipes. He’s a catholic converter.”", "“He said ‘I’m going to chop off the bottom of one of your trouser legs and put it in a library’. I thought ‘That’s a turn-up for the books.'”", "“And the back of his anorak was leaping up and down, and people were chucking money to him. I said ‘Do you earn a living doing that?’ He said ‘Yes, this is my livelihood.'”", "“I bought some Armageddon cheese today, and it said on the packet ‘Best Before End…'”", "“So this bloke says to me, ‘Can I come in your house and talk about your carpets?’ I thought ‘That’s all I need, a Je-hoover’s witness.'”", "“So Batman came up to me & he hit me over the head with a vase & he went ‘T’PAU!’ I said ‘Don’t you mean KAPOW??’ He said ‘No, I’ve got china in my hand.'”"]
if __name__ == "__main__":
    hamez_and_mazza_halachot = library.get_index("Mishneh Torah, Leavened and Unleavened Bread").all_segment_refs()
    hamez_and_mazza_halachot = [ref.tref + ":\n" + normalizer.normalize(ref.text().as_string()) for ref in hamez_and_mazza_halachot]
    # sorted_halachot = sort_by_instruction(hamez_and_mazza_halachot,
    #                         "We are a Jewish religious family, and we are about to hold a Passsover Seder. My dad asked me to introduce the concept of the Seder night to our guests, whose background in Judaism is not as strong."
    #                         "Given 2 Halakhot taken form Rambam's Mishne Torah, output the index of the one which presents a more introductory-level information about the Passover Seder, which might be suitable for our guests. If both are equally fundamental and introductory-level with regards to the Passover seder, output 0. ")
    sorted_halachot = sort_by_instruction(hamez_and_mazza_halachot,
                                          "You are an expert in Jewish laws and traditions, specifically interested in laws pertaining to unleavened bread (Matzah) during Passover."
                                          "Given 2 Halakhot taken form Rambam's Mishne Torah, output the index of the one which presents a more interesting, sophisticated and non-trivial information regarding the Matzah (unleavened bread), which might be of interest to you as a learned expert. If both are equally non-trivial and interesting with regards to the Matzah, output 0. ")


    for h in sorted_halachot:
        print(h)

    print("bye")

