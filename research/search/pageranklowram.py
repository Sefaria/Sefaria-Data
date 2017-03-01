# Generates a random web link structure, and finds the
# corresponding PageRank vector.  The number of inbound
# links for each page is controlled by a power law
# distribution.
#
# This code should work for up to a few million pages on a
# modest machine.
#
# Written and tested using Python 2.5.

import numpy
import random

class web:
  def __init__(self,n):
    self.size = n
    self.in_links = {}
    self.number_out_links = {}
    self.dangling_pages = {}
    for j in xrange(n):
      self.in_links[j] = []
      self.number_out_links[j] = 0
      self.dangling_pages[j] = True

def paretosample(n,power=2.0):
  '''Returns a sample from a truncated Pareto distribution
  with probability mass function p(l) proportional to
  1/l^power.  The distribution is truncated at l = n.'''
  m = n+1
  while m > n: m = numpy.random.zipf(power)
  return m

def random_web(n=1000,power=2.0):
  '''Returns a web object with n pages, and where each
  page k is linked to by L_k random other pages.  The L_k
  are independent and identically distributed random
  variables with a shifted and truncated Pareto
  probability mass function p(l) proportional to
  1/(l+1)^power.'''
  g = web(n)
  for k in xrange(n):
    lk = paretosample(n+1,power)-1
    values = random.sample(xrange(n),lk)
    g.in_links[k] = values
    for j in values:
      if g.number_out_links[j] == 0: g.dangling_pages.pop(j)
      g.number_out_links[j] += 1
  return g


def create_empty_nodes(g):
  all_links = set(reduce(lambda a, b: a + b, [v.keys() for v in g.values()], []))
  for l in all_links:
    if l not in g:
      g[l] = {}
  return g


def create_web(g):
  #g = create_empty_nodes(g)
  n = len(g)
  w = web(n)
  node2index = {r:i for i, r in enumerate(g.keys())}
  for i, (r, links) in enumerate(g.items()):
    r_ind = node2index[r]
    link_inds = [node2index[r_temp] for r_temp in links]
    w.in_links[r_ind] = link_inds
    for j in link_inds:
      if w.number_out_links[j] == 0: w.dangling_pages.pop(j)
      w.number_out_links[j] += 1
  return w

def step(g,p,s=0.85):
  '''Performs a single step in the PageRank computation,
  with web g and parameter s.  Applies the corresponding M
  matrix to the vector p, and returns the resulting
  vector.'''
  n = g.size
  v = numpy.matrix(numpy.zeros((n,1)))
  inner_product = sum([p[j] for j in g.dangling_pages.keys()])
  for j in xrange(n):
    v[j] = s*sum([p[k]/g.number_out_links[k]
    for k in g.in_links[j]])+s*inner_product/n+(1-s)/n
  # We rescale the return vector, so it remains a
  # probability distribution even with floating point
  # roundoff.
  return v/numpy.sum(v)

def pagerank(g,s=0.85,tolerance=0.00001, maxiter=100, verbose=False):
  w = create_web(g)
  n = w.size
  p = numpy.matrix(numpy.ones((n,1)))/n
  iteration = 1
  change = 2
  while change > tolerance and iteration < maxiter:
    if verbose: print "Iteration: %s" % iteration
    new_p = step(w,p,s)
    change = numpy.sum(numpy.abs(p-new_p))
    if verbose: print "Change in l1 norm: %s" % change
    p = new_p
    iteration += 1
  pr_list = list(numpy.squeeze(numpy.asarray(p)))
  return {k:v for k,v in zip(g.keys(), pr_list)}


g = random_web(100,2.0) # works up to several million
                          # pages.


#g = {'a':{'b':1,'c':1,'d':1},'b':{'d':1},'c':{'b':1,'d':1},'d':{}}
#pr = pagerank(g, 0.85, 0.0001)
#print pr
#pass