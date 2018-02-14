# -*- coding: utf-8 -*-

import os
folders_in_order = ['בראשית','שמות','ויקרא','במדבר','דברים']
base_text_files = ['שאילתות בראשית.txt','שאילתות שמות.txt','שאילתות ויקרא.txt','שאילתות במדבר.txt','שאילתות דברים.txt']
sheiltot = [[] for x in range(171)]
folder_names=[x[0]for x in os.walk("files")][1:]
for folder in folder_names:
    for _file in os.listdir(folder):
        if _file in base_text_files:
            sheilta_box = []
            current_sheilta = 0
            with open(folder+'/'+_file) as myfile:
                lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
            for line in lines:
                if u'@22' in line:
                    current_sheilta
                


