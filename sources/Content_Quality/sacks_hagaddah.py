import django

django.setup()

from sefaria.model import *
from sefaria.helper.schema import change_node_title, remove_branch
# from sefaria.helper.schema import *
from sources.functions import post_link


# This script makes some changes to Haggadah commentaries (new collective title, renaming nodes, re-linking)
# It was run on Midrash BeChiddush and the Jonathan Sacks Haggadah.
# Not all of the functions are relevant for each case, but can be adapted for any Haggadah commentary
# that needs shifting. 


def update_simanim_to_seder():
    try:
        node = Ref('The Jonathan Sacks Haggadah, The Simanim').index_node
        change_node_title(snode=node, old_title="The Simanim", lang="en", new_title="The Seder")
        change_node_title(snode=node, old_title="סימני הסדר", lang="he", new_title="הקדמה")

    except Exception as e:
        print(e)
        print("Already complete, skipping")



def delete_grandnode(parent_title, child_key):
    grandnode = Ref(f'The Jonathan Sacks Haggadah, {parent_title}, {child_key}').index_node
    remove_branch(grandnode)


def delete_empty_nodes(jsh_index):
    for node_key in ["Rachtzah", "Maror", "Shulchan Orech"]:
        try:
            snode = Ref(f"The Jonathan Sacks Haggadah, {node_key}").index_node
            remove_branch(snode)
        except Exception as e:
            print(e)


    # Magid
    delete_grandnode("Magid", "In the Beginning Our Fathers Were Idol Worshipers")

    # Barech
    delete_grandnode("Barech", "Third Cup of Wine")

    # Hallel
    delete_grandnode("Hallel", "Second Half of Hallel")
    delete_grandnode("Hallel", "Songs of Praise and Thanks")
    delete_grandnode("Hallel", "Fourth Cup of Wine")

    # Nirtzah
    delete_grandnode("Nirtzah", "Sefirat HaOmer")


if __name__ == '__main__':

    index_title_en = "Midrash BeChiddush on Pesach Haggadah"
    index_title_he = u"מדרש בחדוש"
    term_name = "Midrash BeChiddush"

    jsh_index = Index().load({'title': index_title_en})

    # Create collective title
    jsh_term = Term().load({'name': "Midrash BeChidush"})
    if jsh_term:
        jsh_term.delete()
    jsh_term = Term().load({'name': term_name})

    if not jsh_term:
        t = Term()
        t.name = term_name
        t.add_primary_titles(index_title_en, index_title_he)
        t.save()

    if jsh_index:
        jsh_index.collective_title = term_name
        jsh_index.set_title(index_title_en)
        jsh_index.save()
        node = Ref(jsh_index.title).index_node
        change_node_title(snode=node,
                          old_title="Midrash BeChidush on Pesach Haggadah",
                          lang="en",
                          new_title=index_title_en)




    jsh_index = Index().load({"title": index_title_en})
    print(f"collective: {jsh_index.collective_title}")
    print(f"key: {jsh_index.nodes.key}")
    print(f"title: {jsh_index.title}")

    update_simanim_to_seder()

    jsh_index = Index().load({"title": index_title_en})

    # Specific to Sacks change, testing if it worked
    # try:
    #     r = Ref("The Jonathan Sacks Haggadah, The Seder")
    #     print(f"Update complete for {r.normal()}")
    # except Exception as e:
    #     print("ERROR: Schema title update did not complete")
    #     print(e)


    ## TODO At this point, manually delete the empty nodes Shmuel request to edit (using EDIT)

    # Ghost links and relink
    # Delete all existing links between Jonathan sacks Hagaddah and Hagddah

    ls = LinkSet({'refs': {"$regex": "Midrash BeChiddush"}})
    for l in ls:
        if "Pesach Haggadah" in l.refs[0] or "Pesach Haggadah" in l.refs[1]:
            print("link deleted")
            l.delete()

    jsh_section = Ref("Midrash BeChiddush on Pesach Haggadah").first_available_section_ref()
    while jsh_section:

        print(jsh_section)

        hgda_ref = jsh_section.as_ranged_segment_ref().normal()
        pesach_ref = hgda_ref.replace("Midrash BeChiddush on ", "")
        pesach_ref = pesach_ref.split(":")[0]
        print(pesach_ref)

        # Create new link....
        link = {
            'refs': [hgda_ref, pesach_ref],
            'type': 'Commentary',
            'auto': True
        }

        print(link)

    # TODO - on cauldron just manually move over links in Studio 3T
        post_link(link)

        jsh_section = jsh_section.next_section_ref()

