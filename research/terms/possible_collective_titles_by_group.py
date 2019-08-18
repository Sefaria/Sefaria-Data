
#prints out list of word appearances in index titles, along with the second most commonly appearing word per word grouping

indices_by_word = {}
num_by_word = {}

for index in library.all_index_records():
    try:
        index.collective_title
    except AttributeError:
        for word in index.get_title().split():
            if word in indices_by_word.keys():
                indices_by_word[word].append(index)
                num_by_word[word] += 1
            else:
                indices_by_word[word] = [index]
                num_by_word[word] = 1

import operator
sorted_x = sorted(num_by_word.items(), key=operator.itemgetter(1), reverse=True)

indices_by_word2 = {}
num_by_word2 = {}
lists1 = {}
lists2 = {}

for word1, indices in indices_by_word.items():
    for index in indices:
        for word in index.get_title().split():
            if word == word1:
                continue
            if word in indices_by_word2.keys():
                indices_by_word2[word].append(index)
                num_by_word2[word] += 1
            else:
                indices_by_word2[word] = [index]
                num_by_word2[word] = 1
    lists1[word1] = indices_by_word2
    lists2[word1] = num_by_word2
    indices_by_word2 = {}
    num_by_word2 = {}

to_print = {}
for word, num_list in lists2.items():
    new_num_list = {key: value for key,value in num_list.items() if value > 1}
    sorted_z = sorted(new_num_list.items(), key=operator.itemgetter(1), reverse=True)
    to_print[("{} ({}), {}".format(word, num_by_word[word], sorted_z))] = num_by_word[word]

sorted_final = sorted(to_print.items(), key=operator.itemgetter(1), reverse=True)
for string, num in sorted_final:
    print string
print
print
for word, num in sorted_x:
    print "\"{}\" was found {} times in the following indices : {}".format(word, num_by_word[word], indices_by_word[word])
