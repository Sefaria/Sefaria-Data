import django

django.setup()

superuser_id = 171118


def handle_index_kinnim():
    from sources.functions import post_index
    index = post_index({'title': 'Raavad on Mishnah Kinnim'}, server='https://piaseczno.cauldron.sefaria.org', method='GET')
    print(index)
    index['collective_title'] = "Raavad"
    index["dependence"] = "Commentary"
    index["base_text_titles"] = ["Mishnah Kinnim"]
    post_index(index, server='https://piaseczno.cauldron.sefaria.org')

def handle_index_demai():
    from sources.functions import post_index
    index = post_index({'title': 'Raavad on Mishnah Demai'}, server='https://piaseczno.cauldron.sefaria.org', method='GET')
    print(index)
    index['collective_title'] = "Raavad"
    index["dependence"] = "Commentary"
    index["base_text_titles"] = ["Mishnah Demai"]
    post_index(index, server='https://piaseczno.cauldron.sefaria.org')



if __name__ == '__main__':
    print("hello")
    # handle_index_kinnim()
    handle_index_demai()