#encoding=utf-8
import numpy as np
import pandas as pd
from os import path
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from collections import Counter
import matplotlib.pyplot as plt
from sources.functions import UnicodeWriter

with open("words.txt") as f:
    words = dict(Counter(list(f)[0].decode('utf-8').split()))
    words = [(k, unicode(v)) for k, v in words.iteritems()]
    with open("out.txt", 'w') as f2:
        writer = UnicodeWriter(f2)
        writer.writerows(words)
    print words
    wordcloud = WordCloud(regexp=r"[\u05d0–\u05ea]").generate_from_frequencies(words)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()


