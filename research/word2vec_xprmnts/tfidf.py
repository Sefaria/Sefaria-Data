#!/usr/bin/env python

"""
The simplest TF-IDF library imaginable.

Add your documents as two-element lists `[docname, [list_of_words_in_the_document]]` with `addDocument(docname, list_of_words)`. Get a list of all the `[docname, similarity_score]` pairs relative to a document by calling `similarities([list_of_words])`.

See the README for a usage example.
"""

import sys
import os, heapq, math
import numpy as np
from collections import OrderedDict

class tfidf:
  def __init__(self, all_words):
    self.weighted = False
    self.documents = OrderedDict()
    self.corpus_dict = OrderedDict()
    self.all_words = list(all_words)
    self.word2int = {}
    self.axis_dot_prod_mat = None
    for i, w in enumerate(all_words):
      self.word2int[w] = i


  @staticmethod
  def argmax(iterable, n=1):
    if n == 1:
      return max(enumerate(iterable), key=lambda x: x[1])[0]
    else:
      return heapq.nlargest(n, xrange(len(iterable)), iterable.__getitem__)

  def addDocument(self, doc_obj, list_of_words):
    # building a dictionary
    doc_list = np.zeros((len(self.all_words,)))
    for w in list_of_words:
      word_ind = self.word2int[w]
      doc_list[word_ind] += 1
      self.corpus_dict[w] = self.corpus_dict.get(w, 0.0) + 1.0

    # normalizing the dictionary
    doc_list /= float(len(list_of_words))

    # add the normalized document to the corpus
    self.documents[doc_obj] = doc_list

  def finalize(self):
    num_docs = float(len(self.documents))
    for w, wc in self.corpus_dict.items():
      temp_idf = 1 + math.log(num_docs / self.corpus_dict[w])
      for k, doc_list in self.documents.items():
        doc_list[self.word2int[w]] *= temp_idf

  def get_n_mvv(self, v1, v2, n):
    dot_products = np.abs(v1 + v2)
    return self.argmax(dot_products, n)

  def similarity_out_of_tanakh(self, list_of_words, top_n_words):
    doc_list = np.zeros((len(self.all_words, )))
    for w in list_of_words:
      word_ind = self.word2int[w]
      doc_list[word_ind] += 1
      self.corpus_dict[w] = self.corpus_dict.get(w, 0.0) + 1.0
    # normalizing the dictionary
    doc_list /= float(len(list_of_words))

    num_docs = float(len(self.documents))
    for w, wc in self.corpus_dict.items():
      temp_idf = 1 + math.log(num_docs / self.corpus_dict[w])
      doc_list[self.word2int[w]] *= temp_idf

    for temp_doc_obj, temp_doc_list in self.documents.items():
      sims = []
      cos_dist = np.dot(doc_list, temp_doc_list) / (np.linalg.norm(doc_list) * np.linalg.norm(temp_doc_list))

      top_n_inds = self.get_n_mvv(doc_list, temp_doc_list, top_n_words*2)
      top_words = []
      for word_ind in top_n_inds:
        if len(top_words) > top_n_words:
          break
        try:
          if temp_doc_obj.words.index(self.all_words[word_ind]):
            top_words += [self.all_words[word_ind]]
        except ValueError:
          pass
      sims += [(temp_doc_obj, cos_dist, top_words)]

  def similarities(self, doc_obj, top_n_words):
    doc_list = self.documents[doc_obj]
    sims = []
    for temp_doc_obj, temp_doc_list in self.documents.items():
      if temp_doc_obj == doc_obj:
        continue
      cos_dist = np.dot(doc_list, temp_doc_list) / (np.linalg.norm(doc_list) * np.linalg.norm(temp_doc_list))

      top_n_inds = self.get_n_mvv(doc_list, temp_doc_list, top_n_words*2)
      top_words = []
      for word_ind in top_n_inds:
        if len(top_words) > top_n_words:
          break
        try:
          if doc_obj.words.index(self.all_words[word_ind]) and temp_doc_obj.words.index(self.all_words[word_ind]):
            top_words += [self.all_words[word_ind]]
        except ValueError:
          pass
      sims += [(temp_doc_obj, cos_dist, top_words)]


    sims.sort(key=lambda x: x[1])
    return sims




    # computing the list of similarities
    sims = []
    # for doc in self.documents:
    #   score_list = []
    #   doc_dict = doc[1]
    #   for k in query_dict:
    #     if k in doc_dict:
    #       score_list += [(query_dict[k] * math.log(float(len(self.corpus_dict))/self.corpus_dict[k])) + (doc_dict[k] / self.corpus_dict[k])]
    #
    #   top_words = []
    #   top_word_inds = self.argmax(score_list, top_n_words)
    #   words = query_dict.keys()
    #   for word_ind in top_word_inds:
    #     top_words += [words[word_ind]]
    #
    #   sims.append([doc[0], sum(score_list), top_words])

    # return sims
