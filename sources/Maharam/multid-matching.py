__author__ = 'stevenkaplan'


ref_title = "Tosafot on Bava Batra 2b"
ref = Ref(ref_title)
ref.normal()[ref.normal().rfind(" ") + 1:]
ref_data_array = ref.get_state_ja("he").array()[3]
new_refs = []
for first_level_count, ref_data in enumerate(ref_data_array):
    for second_level_count, each_one in enumerate(ref_data):
        new_refs.append(ref_title + ":" + str(first_level_count + 1) + ":" + str(second_level_count + 1))

