import requests

# Get the Refs for Rashi on Genesis
genesis_refs = requests.get('https://www.sefaria.org/api/index/Rashi_on_Leviticus').json()['alt_structs']['Tanakh Rashi']['nodes']

# Get the Refs for Rashi on Numbers
numbers_refs = requests.get('https://www.sefaria.org/api/index/Rashi_on_Numbers').json()['alt_structs']['Tanakh Rashi']['nodes']

# Iterate through each ref in Genesis and search for the same ref in Numbers
links = []
for ref in genesis_refs:
    for num_ref in numbers_refs:
        if ref['sharedTitle'] == num_ref['sharedTitle']:
            links.append({'genesis': ref['sectionRef'], 'numbers': num_ref['sectionRef']})

# Output the links
print(links)