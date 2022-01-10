for ind in IndexSet({'title':{'$regex':'^Jerusalem Talmud'}}):
    tit = ind.title
    if 'Shekalim' in tit:
        tit=tit.replace('Jerusalem Talmud', 'JTmock')
        ind=library.get_index(tit)
        ind.alt_structs['Vilna']['nodes'][6]['refs'][4] = 'JTmock Shekalim 7:3:3-6'
        ind.alt_structs['Vilna']['nodes'][6]['refs'][5] = 'JTmock Shekalim 7:3:6-8'
        ind.alt_structs['Vilna']['nodes'][6]['refs'][6] = 'JTmock Shekalim 7:3:8-12'
    elif 'Terumot' in tit:
        ind.alt_structs['Vilna']['nodes'][0]['refs'][1] = 'Jerusalem Talmud Terumot 1:1:4-8'
        ind.alt_structs['Vilna']['nodes'][0]['refs'][2] = 'Jerusalem Talmud Terumot 1:1:8-12'
        ind.alt_structs['Vilna']['nodes'][0]['refs'][3] = 'Jerusalem Talmud Terumot 1:1:12-14'
        ind.alt_structs['Vilna']['nodes'][0]['refs'][4] = 'Jerusalem Talmud Terumot 1:1:15-16'
        ind.alt_structs['Vilna']['nodes'][0]['refs'][5] = 'Jerusalem Talmud Terumot 1:1:16-18'
        ind.alt_structs['Vilna']['nodes'][0]['refs'][6] = 'Jerusalem Talmud Terumot 1:1:19-21'
        ind.alt_structs['Vilna']['nodes'][0]['refs'][7] = 'Jerusalem Talmud Terumot 1:1:22-23'
        ind.alt_structs['Vilna']['nodes'][0]['refs'][8] = 'Jerusalem Talmud Terumot 1:1:23-2:3'
    elif 'Megillah' in tit:
        ind.alt_structs['Vilna']['nodes'][0]['refs'][-2] = 'Jerusalem Talmud Megillah 1:12:5-8'
        ind.alt_structs['Vilna']['nodes'][0]['refs'][-1] = 'Jerusalem Talmud Megillah 1:12:8-9'
    for a in ['Venice', 'Vilna']:
        for n in ind.alt_structs[a]['nodes']:
            for i, ref in enumerate(n['refs'][1:], 1):
                ref = Ref(ref).starting_ref()
                t = ref.text('he').text
                if a not in t:
                    old_ref = ref.normal()
                    if a in ref.next_segment_ref().text('he').text:
                        ref = ref.next_segment_ref().normal()
                    elif a in ref.prev_segment_ref().text('he').text:
                        ref = ref.prev_segment_ref().normal()
                    else:
                        ref = ref.normal().replace('6:3', '7:2')
                    new = n['refs'][i].replace(old_ref, ref)
                    new = Ref(new).normal()
                    print(f"changing {n['refs'][i]} to {new}")
                    n['refs'][i] = new
                    end = Ref(n['refs'][i-1]).ending_ref().normal()
                    if end == old_ref:
                        new = f"{n['refs'][i-1].split('-')[0]}-{ref.split()[-1]}"
                        new = Ref(new).normal()
                        print(f"changing {n['refs'][i-1]} to {new}")
                        n['refs'][i-1] = new
    ind.save()
