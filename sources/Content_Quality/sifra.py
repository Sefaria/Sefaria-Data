import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import change_node_title, cascade

bad_to_good = """Braita d'Rabbi Yishmael>Baraita DeRabbi Yishmael
Vayikra Dibbura d'Nedavah>Vayikra Dibbura DeNedavah
Vayikra Dibbura d'Chovah>Vayikra Dibbura DeChovah
Mechilta d'Miluim 1>Mekhilta DeMiluim I
Mechilta d'Miluim 2>Mekhilta DeMiluim II
Tazria Parashat Nega'im>Tazria Parashat Negaim""".splitlines()

def change_title(i, node, old_ref, old_full_ref, new_full_ref):
    def needs_rewrite(x, *args):
        return x.startswith(old_full_ref)
    change_node_title(node, old_ref, 'en', bad_to_good_dict[old_ref], ignore_cascade=True)
    rewriter = lambda x: x.replace(old_full_ref, new_full_ref)
    cascade(f"{i}", rewriter=rewriter, needs_rewrite=needs_rewrite)

bad_to_good_dict = {}
for x in bad_to_good:
    bad_to_good_dict[x.split(">")[0]] = x.split(">")[1]
for i in ["Sifra", "Chafetz Chaim on Sifra"]:
    nodes = library.get_index(i).nodes.children
    for n in nodes:
        print(n)
        old_ref = n.get_primary_title()
        if old_ref in bad_to_good_dict:
            change_title(i, n, old_ref, n.ref().normal(), f"{i}, {bad_to_good_dict[old_ref]}")
        for sub_n in n.children:
            print(sub_n)
            old_ref = sub_n.get_primary_title()
            if old_ref in bad_to_good_dict:
                change_title(i, sub_n, old_ref, sub_n.ref().normal(), f"{n}, {bad_to_good_dict[old_ref]}")

