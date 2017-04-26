def ch_post_term(comm_name):
    term_obj = {
        "name": comm_name,
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": comm_name,
                "primary": True
            },
            {
                "lang": "he",
                "text": u'תוספות רי\"ד',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
posting_term = True
posting_index = True
posting_text=True
linking = True
com_dic = {"Lev Levanon":{"he_title":u"לב לבנון",
                           "file_name":"חובת הלבבות לב לבנון.txt"},
            "Pat Lehem":{"he_title":u"פת לחם",
                        "file_name":"חובת הלבבות פת לחם.txt"},
            "Merapei Lanefesh":{"he_title":u"מרפא לנפש",
                                "file_name":"חובת הלבבות מרפא לנפש.txt"}
                           
eng_names = ["Lev Levnon","M","P"]
for file in com_file_names:
    if posting_term:
        
    