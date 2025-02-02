import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import change_node_title






if __name__ == '__main__':
    index = library.get_index("Siddur Ashkenaz")
    ref = Ref("Siddur_Ashkenaz,_Weekday,_Shacharit,_Torah_Reading,_Returning_Sefer_to_Aron")
    index_node = ref.index_node
    change_node_title(index_node, "הכנסת תפילה", "he", "הכנסת ספר תורה")

    print("bye")

