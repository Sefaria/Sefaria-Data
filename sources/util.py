__author__ = 'stevenkaplan'
class Util:

def in_order_multiple_segments(line, curr_num, increment_by):
     if len(line) > 0 and line[0] == ' ':
         line = line[1:]
     if len(line) > 0 and line[len(line)-1] == ' ':
         line = line[:-1]
     if len(line.split(" "))>1:
         all = line.split(" ")
         num_list = []
         for i in range(len(all)):
             num_list.append(getGematria(all[i]))
         num_list = sorted(num_list)
         for poss_num in num_list:
             poss_num = fixChetHay(poss_num, curr_num)
             if poss_num < curr_num:
                 return -1
             else:
                 curr_num = poss_num
     return curr_num

def fixChetHay(poss_num, curr_num):
    if poss_num == 8 and curr_num == 4:
        return 5
    elif poss_num == 5 and curr_num == 7:
        return 8
    else:
        return poss_num

def in_order(list, tag, reset_tag, output_file='in_order.txt', multiple_segments=False, dont_count=[], increment_by=1):
     poss_num = 0
     curr_num = 0
     perfect = True
     for line in list:
         for word in dont_count:
            line = line.replace(word, "")
         if line.find(tag)>=0:
             if multiple_segments == True:
                 curr_num = in_order_multiple_segments(line, curr_num, increment_by)
             else:
                 poss_num = getGematria(line)
                 poss_num = fixChetHay(poss_num, curr_num)
                 if increment_by > 0:
                     if poss_num - curr_num != increment_by:
                         perfect = False
                 if poss_num < curr_num:
                     perfect = False
                 curr_num = poss_num
                 if perfect == False:
                     pdb.set_trace()
                 prev_line = line