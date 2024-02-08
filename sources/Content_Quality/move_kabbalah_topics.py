import django
django.setup()
from sefaria.model import *
r = Ref("Avot D'Rabbi Natan 3")

def custom_func(item):
    return item.get_primary_title('en').replace("Ḥ", "Ch")

k = Topic.init('kabbalah')
k.isTopLevelDisplay = True
k.displayOrder = 85
k.save()
# for t in TopicSet({'titles.text': {"$regex": "\(Kabbalah"}}):
#     for i, title in enumerate(t.titles):
#         t.titles[i]['disambiguation'] = "Kabbalah"
#         t.titles[i]['text'] = t.titles[i]['text'].replace(" (Kabbalah)", "")
#     t.save()
for t in TopicSet({'titles.disambiguation': 'Kabbalah'}):
    link = {"toTopic": "kabbalah", "fromTopic": t.slug, "linkType": "displays-under", "dataSource": "sefaria"}
    if IntraTopicLink().load(link) is None:
        print(f"Creating new link {t.slug}")
        new_link = IntraTopicLink(link)
        new_link.save()
    if 'Ḥ' in t.get_primary_title('en') or "ḥ" in t.get_primary_title('en'):
        for title in t.titles:
            title["text"] = title["text"].replace('Ḥ', "Ch").replace("ḥ", "ch")
        t.save()


topics = TopicSet({'titles.disambiguation': 'Kabbalah'}).array()
topics.sort(key=custom_func)
for i, t in enumerate(topics):
    print(t.slug)
    t.displayOrder = i * 10
    t.save()

topics = TopicSet({'titles.disambiguation': 'Kabbalah'}).array()
for t in topics:
    t.description['en'] = t.description['en'].replace("Ḥ", "Ch").replace("ḥ", "ch")
    t.save()
#
# topics = {"tiferet1": "The [sefira](/topics/sefirot) of *Tiferet* is the sixth of the ten [sefirot](/topics/sefirot). When the [sefirot](/topics/sefirot) are divided into the five primary [sefirot](/topics/sefirot)  – [Keter](/topics/keter1), [*Ḥokhma*](/topics/hokhma), [Bina](/topics/bina2), [Tiferet](/topics/tiferet1), and [Malkhut](/topics/malkhut1) –*Tiferet* is parallel to the third [level](/topics/level) of the direct light of giving emanating from the Creator. This [level](/topics/level) of light is primarily drawn from the desire of the created beings to bond with the Creator, a will to give, but it also contains a certain amount of the will to receive the light of the Creator, which draws in illuminations from the light of wisdom.  *Tiferet* means “Beauty” (the concept of harmony), and it is called by this name because it is able to integrate both kinds of light within it, the light of wisdom, and the light of giving. This integration, which can be thought of as being formed of two columns of light, as well as an intermediating column which connects them, is the harmonious beauty of this *sefira*. It is this integrative capacity and its unique combination of lights that gives *Tiferet* its unique characterization in which the five *sefirot* that comprise it are given different names (recall that each *sefira* is formed of all five *sefirot*): The [Keter](/topics/keter1) in *Tiferet* is called [Ḥesed](/topics/hesed). The [Ḥokhma](/topics/hokhma) in *Tiferet* is called [Gevura](/topics/gevura). The [Bina](/topics/bina2) in *Tiferet* is called *Tiferet*. The *Tiferet* within *Tiferet* is called *Netzaḥ*. The [Malkhut](/topics/malkhut1) within *Tiferet* is called [Hod](/topics/hod1). In addition to these five, there is a sixth [sefira](/topics/sefirot) in *Tiferet* called [Yesod](/topics/yesod1), which includes the preceding five within it. It is this grouping of the [sefirot](/topics/sefirot) that gives rise to the familiar count of ten [sefirot](/topics/sefirot).  In the structure of [partzufim](/topics/partzuf), *Tiferet* is considered the [body](/topics/body2) of the [partzuf](/topics/partzuf). Two hands ([Ḥesed](/topics/hesed) and [Gevura](/topics/gevura)) emerge from the [body](/topics/body2), as well as two legs ([Netzaḥ](/topics/netzah) and [Hod](/topics/hod1)) and the limb of procreation and life ([Yesod](/topics/yesod1)), thus forming the image of the human body. The [partzuf](/topics/partzuf) that correlates to *Tiferet* is [Ze’er Anpin](/topics/zeer-anpin), which encompasses the [six extremities](/topics/six-extremities). Each of the five primary [sefirot](/topics/sefirot) is also parallel to one of the five worlds that form existence. The world that correlates to the [sefira](/topics/sefirot) of *Tiferet* is the world of [Yetzira](/topics/yetzira1).",
# "hesed": "The [sefira](/topics/sefirot) of *Ḥesed* is the fourth of the ten [sefirot](/topics/sefirot). When the [sefirot](/topics/sefirot) are divided into the five primary [sefirot](/topics/sefirot)  – [Keter](/topics/keter1), [*Ḥokhma*](/topics/hokhma), [Bina](/topics/bina2), [Tiferet](/topics/tiferet1), and [Malkhut](/topics/malkhut1)  – *Ḥesed* is encompassed in the [sefira](/topics/sefirot) of [Tiferet](/topics/tiferet1) as the [Keter](/topics/keter1) [level](/topics/level) of [Tiferet](/topics/tiferet1) (see [Tiferet](/topics/tiferet1)). The term *sefirat* *Ḥesed* is also a reference to different [levels](/topics/level) and *sefirot* in lower structures of reality that are all derivatives of the root *sefira* of *Ḥesed* found in the direct light. This [sefira](/topics/sefirot) is called *Ḥesed* because it contains the light of giving (*ḥassadim*) that emanates from the [sefira](/topics/sefirot) of [Bina](/topics/bina2), which precedes *Ḥesed*, the light that is the essence of giving and bestowal on the part of a created being and that did not undergo any constriction. In the structure of [partzufim](/topics/partzuf), which is analogous to the human body, *Ḥesed* is always presented as the right hand of the *partzuf*, the hand that represents bestowal and closeness.",
# "hod1": "The [sefira](/topics/sefirot) of *Hod* is the eighth of the ten [sefirot](/topics/sefirot). When the [sefirot](/topics/sefirot) are divided into the five primary [sefirot](/topics/sefirot) – [Keter](/topics/keter1), [*Ḥokhma*](/topics/hokhma), [Bina](/topics/bina2), [Tiferet](/topics/tiferet1), and [Malkhut](/topics/malkhut1) – *Hod* is encompassed in the [sefira](/topics/sefirot) of [Tiferet](/topics/tiferet1) as the [Malkhut](/topics/malkhut1) [level](/topics/level) for the [sefira](/topics/sefirot) of [Tiferet](/topics/tiferet1).  *Hod* is the [sefira](/topics/sefirot) which completes the left line or column in every [partzuf](/topics/partzuf) or world. Its essence is that of the fourth [level](/topics/level) ([Malkhut](/topics/malkhut1)). Because of this, and its role of completion, the [sefira](/topics/sefirot) of *Hod* is considered female, and possessing the attribute of judgment. The name *Hod* derives from the word *hoda’ah*, thanksgiving, because the feminine (the left side) is grateful for the light that the masculine (the right side) shines on it. This light is the light of giving, which carries the light of wisdom with it, light, which was restricted as a result of the first [constriction](/topics/tzimtzum1). In the structure of the [partzufim](/topics/partzuf), which correlates with the human body, the [sefira](/topics/sefirot) of *Hod* is associated with the left thigh or leg.",
# "yesod1": "The [sefira](/topics/sefirot) of *Yesod* is the ninth of the ten [sefirot](/topics/sefirot). When the [sefirot](/topics/sefirot) are divided into the five primary [sefirot](/topics/sefirot) – [Keter](/topics/keter1), [*Ḥokhma*](/topics/hokhma), [Bina](/topics/bina2), [Tiferet](/topics/tiferet1), and [Malkhut](/topics/malkhut1) – *Yesod* is encompassed in the [sefira](/topics/sefirot) of [Tiferet](/topics/tiferet1).  *Yesod* is the [sefira](/topics/sefirot) that represents the end of the middle line or column, the line of [Tiferet](/topics/tiferet1). Accordingly, *Yesod* is a unique aspect of the [sefira](/topics/sefirot) of [Tiferet](/topics/tiferet1) and also exists in parallel in the [sefira](/topics/sefirot) of [Malkhut](/topics/malkhut1), which receives the lights of [Tiferet](/topics/tiferet1). *Yesod*, which means “Foundation,” is named thus because it includes the “foundations” of its [level](/topics/level), meaning the various lights within that [level](/topics/level). It then transmits these lights to the [sefira](/topics/sefirot) of [Malkhut](/topics/malkhut1) below it, so that *Yesod* serve as the foundation for the existence of the feminine aspect of the [level](/topics/level). In the structure of [partzufim](/topics/partzuf), which correlate to the human body, the [sefira](/topics/sefirot) of *Yesod* represents the sexual reproductive organs.",
# "partzuf": "A *partzuf* is a configuration of the [sefirot](/topics/sefirot) into more complex structures that serve to reveal the divine light that emanates from the Creator in a way that the created entities can receive it. A [sefira](/topics/sefirot) can be thought of as a basic building block of the structure called *partzuf*. Although *partzuf* literally means “countenance” or “face,” it is actually composed of a [head](/topics/head1), a [body](/topics/body2), and legs, similar to the structure of a human body. A *partzuf* is formed as a result of a [fusion through collision](/topics/fusion-through-collision), where the [returning light](/topics/returning-light) from the collision  [enclothes](/topics/enclothe) the supernal light, forming a new structure that reflects the qualities and amounts of the supernal light [enclothed](/topics/enclothe) in the [returning light](/topics/returning-light). In each of the five worlds in reality – [Adam Kadmon](/topics/adam-kadmon1), [Atzilut](/topics/atzilut), [Beria](/topics/beria), [Yetzira](/topics/yetzira1), and [Asiya](/topics/asiya1) – there are five *partzufim*, corresponding to the five primary [sefirot](/topics/sefirot): [Keter](/topics/keter1), [*Ḥokhma*](/topics/hokhma), [*Bina*](/topics/bina2), [*Tiferet*](/topics/tiferet1), and [Malkhut](/topics/malkhut1)."}
# for slug in topics:
#     topic = Topic.init(slug)
#     topic.description['en'] = topics[slug]
#     topic.save()
