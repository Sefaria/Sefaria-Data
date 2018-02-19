from research.mesorat_hashas_sefaria.mesorat_hashas import *
pm = ParallelMatcher(tokenize_words)

#pm.match(index_list=get_texts_from_category("Debug"), parallelize=False, all_to_all=True, use_william=True, verbose=True)
print '-----FILTERING PASUKIM'
#filter_pasuk_matches("All","mesorat_hashas_indexes.json")
print '-----FILTERING CLOSE MATCHES'
#filter_close_matches("mesorat_hashas_pasuk_filtered.json", filter_only_talmud=True)
#remove_mishnah_talmud_dups('mesorat_hashas_clustered.json')
#save_links_local('All','mesorat_hashas_mishnah_filtered.json')
#save_links_post_request('All')
#compare_mesorat_hashas('mesorat_hashas_mishnah_filtered.json','mesorat_hashas_mishnah_filtered_talmud.json')
#get_diff_ids('mesorat_hashas_mishnah_filtered.json','sefaria_noa.links.json')
#bulk_delete('mesorat_hashas_comparison.json')

#sort_n_save('all/mesorat_hashas_mishnah_filtered.json')
#count_cats('all/mesorat_hashas_mishnah_filtered.json')
#daf_with_most_links('all/mesorat_hashas_mishnah_filtered.json')
pm.init_hashtable_for_full_library()
