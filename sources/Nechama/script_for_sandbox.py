i = library.get_index("Midrash Tanchuma")
node = i.nodes.children[2]
node.add_title("Midrash Tanchuma, Genesis", 'en')
i.save()
i = library.get_index("Gur Aryeh on Bereishit")
i.nodes.add_title("Gur Aryeh on Genesis", 'en')
i.save()