"""
This modules provides commonly-used tools for functional programming.

Other modules/functions that might be of interest for functional-paradigm
programmers:
    + the built-in functions `max`, `min`, `lambda`, `map` and `filter`
    + the `operator` module
"""

#################################################################
### The C version of partial originally by Hye-Shik Chang <perky@FreeBSD.org>
### with adaptations by Raymond Hettinger <python@rcn.com>
### translated into Python by Collin Winter <collinw@gmail.com>
###
### All other function definitions translated to Python by
### Collin Winter from the Haskell originals found in the
### Haskell 98 Report, edited by Simon Peyton-Jones <simonpj@microsoft.com>
###
### Copyright (c) 2004-2006 Python Software Foundation.
### All rights reserved.
#################################################################

### partial class
###
### This handles partial function application
#################################################################

class partial(object):
    """
    partial(func, *args, **keywords) - new function with partial application
	of the given arguments and keywords.
    """
    def __init__(self, func, *args, **kwargs):
        if not callable(func):
            raise TypeError("the first argument must be callable")

        self.func = func
        self.args = tuple(args)
        self.kwargs = dict(kwargs)
        self._dict = None

    def __call__(self, *args, **kwargs):
        applied_args = self.args + args

        applied_kwargs = dict(self.kwargs)
        applied_kwargs.update(kwargs)

        return self.func(*applied_args, **applied_kwargs)

    def _getdict(self):
        if self._dict is None:
            return dict()

    def _setdict(self, val):
        assert isinstance(val, dict)

        self._dict = val

    def _deldict(self):
        raise TypeError("a partial object's dictionary may not be deleted")

    __dict__ = property(_getdict, _setdict, _deldict)
    
### compose
#################################################################

def compose(func_1, func_2):
    """
    compose(func_1, func_2) -> function
    
    The function returned by compose is a composition of func_1 and func_2.
    That is, compose(func_1, func_2)(5) == func_1(func_2(5))
    """
    if not callable(func_1):
        raise TypeError("First argument to compose must be callable")
    if not callable(func_2):
        raise TypeError("Second argument to compose must be callable")
    
    def composition(*args, **kwargs):
        return func_1(func_2(*args, **kwargs))
    return composition

### foldl
#################################################################
			
def _foldl(func, base, itr):
    try:
        first = itr.next()
    except StopIteration:
        return base

    return _foldl(func, func(base, first), itr)

def foldl(func, start, itr):
    """
    foldl(function, start, iterable) -> object

    Takes a binary function, a starting value (usually some kind of 'zero'), and
    an iterable. The function is applied to the starting value and the first
    element of the list, then the result of that and the second element of the
    list, then the result of that and the third element of the list, and so on.
    
    foldl(add, 0, [1, 2, 3]) is equivalent to add(add(add(0, 1), 2), 3)
    """
    return _foldl(func, start, iter(itr))

### foldr
#################################################################

def _foldr(func, base, itr):
	try:
		first = itr.next()
	except StopIteration:
		return base
		
	return func(first, _foldr(func, base, itr))

def foldr(func, start, itr):
    """
    foldr(function, start, iterable) -> object
    
    Like foldl, but starts from the end of the iterable and works back toward the
    beginning. For example, foldr(subtract, 0, [1, 2, 3]) == 2, but
    foldl(subtract, 0, [1, 2, 3] == -6
    
    foldr(add, 0, [1, 2, 3]) is equivalent to add(1, add(2, add(3, 0)))
    """
    return _foldr(func, start, iter(itr))
    
### foldl1
#################################################################
			
def foldl1(func, itr):
    """
    foldl1(function, iterable) -> object
    
    Like foldl, but can only operate on non-empty lists.
    """
    itr = iter(itr)

    try:
        first = itr.next()
    except StopIteration:
        raise ValueError("Cannot run foldl1 on an empty list")
    
    return _foldl(func, first, itr)

### foldr1
#################################################################

def foldr1(func, itr):
    """
    foldr1(function, iterable) -> object
    
    Like foldr, but can only operate on non-empty lists.
    """
    itr = iter(itr)
    
    try:
        first = itr.next()
    except StopIteration:
        raise ValueError("Cannot run foldr1 on an empty list")
    
    return _foldr(func, first, itr)

### scanl
#################################################################

def _scanl(func, base, itr):
    """
    In Haskell:
    
    scanl        :: (a -> b -> a) -> a -> [a] -> [a]
    scanl f q xs =  q : (case xs of
                              [] -> []
                            x:xs -> scanl f (f q x) xs)
    """
    yield base
    
    for o in itr:
        base = func(base, o)
        yield base
    raise StopIteration

def scanl(func, start, itr):
    """
    scanl(func, start, iterable) -> iterator
    
    Like foldl, but produces a list of successively reduced values, starting
    from the left.
    scanr(f, 0, [1, 2, 3]) is equivalent to
    [0, f(0, 1), f(f(0, 1), 2), f(f(f(0, 1), 2), 3)]
    
    scanl returns a iterator over the result list. This is done so that the
    list may be calculated lazily.
    """
    if not callable(func):
        raise TypeError("First argument to scanl must be callable")
    itr = iter(itr)

    return _scanl(func, start, itr)
    
### scanl1
#################################################################

def scanl1(func, itr):
    """
    scanl1(function, iterable) -> object
    
    Like scanl, but can only operate on non-empty lists.
    """

    if not callable(func):
        raise TypeError("First argument to scanl1 must be callable")
    itr = iter(itr)
    
    try:
        first = itr.next()
    except StopIteration:
        return iter([])
        
    return _scanl(func, first, itr)

### scanr
#################################################################

def _scanr(func, q0, x_xs):
    """
    In Haskell:
    
    scanr             :: (a -> b -> b) -> b -> [a] -> [b]
    scanr f q0 []     =  [q0]
    scanr f q0 (x:xs) =  f x q : qs
                         where qs@(q:_) = scanr f q0 xs
    """
    
    try:
        # Handle the empty-list condition
        x = x_xs.next()
    except StopIteration:
        yield q0
        raise StopIteration

    qs = _scanr(func, q0, x_xs)

    q = qs.next()
    yield func(x, q)

    # this is the ": qs" from the Haskell definition
    yield q
    while True:
        yield qs.next()

def scanr(func, start, itr):
    """
    scanr(func, start, iterable) -> iterator
    
    Like foldr, but produces a list of successively reduced values, starting
    from the right.
    scanr(f, 0, [1, 2, 3]) is equivalent to
    [f(1, f(2, f(3, 0))), f(2, f(3, 0)), f(3, 0), 0]
    
    scanl returns a iterator over the result list. This is done so that the
    list may be calculated lazily.
    """
    if not callable(func):
        raise TypeError("First argument to scanr must be callable")
    itr = iter(itr)
    
    return _scanr(func, start, itr)
    
### scanr1
#################################################################

def scanr1(func, itr):
    """
    scanr1(function, iterable) -> object
    
    Like scanr, but can only operate on non-empty lists.
    """

    if not callable(func):
        raise TypeError("First argument to scanl1 must be callable")
    itr = iter(itr)
    
    try:
        first = itr.next()
    except StopIteration:
        return iter([])
        
    return _scanr(func, first, itr)

### repeat
#################################################################

def repeat(obj):
    """
    repeat(obj) -> iterator
    
    Takes an object and returns an iterator over an infinite list of this
    object.
    """
    while True:
        yield obj

### cycle
#################################################################

def _cycle(first, itr):
    """
    In Haskell:
    
    cycle    :: [a] -> [a]
    cycle [] =  error "Prelude.cycle empty list"
    cycle xs =  xs' where xs' = xs ++ xs'
    """
    # We play this little game with seq because we can't always restart
    # the iterator (e.g., with generators)
    seq = [first]
    yield first

    for o in iter(itr):
        seq.append(o)
        yield o
        
    while True:
        for o in seq:
            yield o
    
def cycle(itr):
    """
    cycle(iterable) -> generator
    
    Take an iterable object and repeat it to infinity. For example,
    cycle([1, 2, 3]) = [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, ...]
    
    cycle returns a generator so this infinite list can be calculated lazily
    """
    itr = iter(itr)
    
    try:
        first = itr.next()
    except StopIteration:
        raise ValueError("Cannot run cycle on an empty list")
        
    return _cycle(first, itr)

### iterate
#################################################################

def _iterate(func, obj):
    """
    In Haskell:
    
    iterate     :: (a -> a) -> a -> [a]
    iterate f x =  x : iterate f (f x)
    """
    while True:
        yield obj
        obj = func(obj)

def iterate(func, obj):
    """
    iterate(function, obj) -> generator
    
    iterate takes a callable and an object and returns a generator. This
    generator will yield repeated applications of `func`; for example,
    iterate(f, 5) is equivalent to [5, f(5), f(f(5)), f(f(f(5))), ...]
    """
    if not callable(func):
        raise TypeError("First argument to iterate must be callable")
        
    return _iterate(func, obj)

### take
################################################################

def _take(n, itr):
    """
    In Haskell:
    
    take                   :: Int -> [a] -> [a]
    take n _      | n <= 0 =  []
    take _ []              =  []
    take n (x:xs)          =  x : take (n-1) xs
    """
    while n > 0:
        yield itr.next()
        n -= 1
    raise StopIteration

def take(n, itr):
    """
    take(n, iterable) -> generator
    
    take takes a number and an iterable and returns a generator. Effectively,
    take is like a flexible version of slicing that works on all iteratables,
    not just sequences. For example:
    take(4, xrange(0, 30, 6)) == [0, 6, 12, 18]
    
    The generator is used so that the resulting list can be calculated lazily.
    """
    n = int(n)
    itr = iter(itr)
    
    return _take(n, itr)
    
### drop
################################################################

def _drop(n, itr):
    """
    In Haskell:
    
    drop                   :: Int -> [a] -> [a]
    drop n xs     | n <= 0 =  xs
    drop _ []              =  []
    drop n (x:xs)          =  drop (n-1) xs
    """
    # Burn the first n items in the iterator
    while n > 0:
        itr.next()
        n-=1

    while True:
        yield itr.next()
        
def drop(n, itr):
    """
    drop(n, iterable) -> generator
    
    drop takes a number and an iterable and returns a generator. Like take,
    drop is like a flexible version of slicing that works on all iteratables,
    not just sequences. For example:
    xrange(0, 30, 6)          == [0, 6, 12, 18, 24]
    drop(2, xrange(0, 30, 6)) == [12, 18, 24]
    
    The generator is used so that the resulting list can be calculated lazily.
    """
    n = int(n)
    itr = iter(itr)
    
    return _drop(n, itr)

### flip
################################################################

def flip(func):
    """
    flip(func) -> function
    
    flip causes `func` to take its first two arguments in reverse order. The
    returned function is a wrapper around `func` that makes this happen.
    """
    if not callable(func):
        raise TypeError("First argument to flip must be callable")
    
    def flipped_func(arg_1, arg_2, *args, **kwargs):
        return func(arg_2, arg_1, *args, **kwargs)
    return flipped_func

### takeWhile
################################################################

def _takeWhile(predicate, itr):
    """
    In Haskell:
    
    takeWhile               :: (a -> Bool) -> [a] -> [a]
    takeWhile p []          =  []
    takeWhile p (x:xs)
                | p x       =  x : takeWhile p xs
                | otherwise =  []
    """
    
    obj = itr.next()
    while predicate(obj):
        yield obj
        obj = itr.next()

def takeWhile(predicate, itr):
    """
    takeWhile(predicate, iterable) -> generator
    
    Like take, except instead of a numeric constant, the length of the
    resulting list is determined by the `predicate` function. The function
    will be passed successive elements from the `iterable` parameter; if
    `predicate` returns a true value, that element goes in the list and we move
    to the next element. As soon as `predicate` returns a false value,
    iteration terminates and the slice is finished.
    
    def pred(a):
        if a < 5: return True
        return False
    
    takeWhile(pred, [3, 4, 5, 6]) == [3, 4]
    """
    if not callable(predicate):
        raise TypeError("First argument to takeWhile must be callable")
    itr = iter(itr)
    
    return _takeWhile(predicate, itr)

### dropWhile
################################################################

def _dropWhile(predicate, itr):
    """
    In Haskell:
    
    dropWhile               :: (a -> Bool) -> [a] -> [a]
    dropWhile p []          =  []
    dropWhile p xs@(x:xs')
                | p x       =  dropWhile p xs'
                | otherwise =  xs
    """
    # burn through the dropped slice
    obj = itr.next()
    while predicate(obj):
        obj = itr.next()
    
    # "otherwise = xs", from above 
    yield obj
    while True:
        yield itr.next()

def dropWhile(predicate, itr):
    """
    dropWhile(predicate, iterable) -> generator
    
    Like drop, except instead of a numeric constant, the length of the
    dropped slice is determined by the `predicate` function. The function
    will be passed successive elements from the `iterable` parameter; if
    `predicate` returns a true value, we move to the next element. As soon
    as `predicate` returns a false value, iteration terminates and the
    remaining portion of the iterable is returned.
    
    def pred(a):
        if a < 5: return True
        return False
    
    dropWhile(pred, [3, 4, 5, 6]) == [5, 6]
    """
    if not callable(predicate):
        raise TypeError("First argument to dropWhile must be callable")
    itr = iter(itr)
    
    return _dropWhile(predicate, itr)

### id
################################################################

def id(obj):
    """
    id(obj) -> object
    
    The identity function. id(obj) returns obj unchanged.
    
    >>> obj = object()
    >>> id(obj) is obj
    True
    """
    return obj

### concat
################################################################

try:
    from operator import add
except ImportError:
    def add(a, b):
        return a + b

def concat(itr):
    """
    concat(iterable) -> list
    
    concat takes an iterable of lists and concatenates the sublists.
    
    >>> concat([[1], [2], [3]])
    [1, 2, 3]
    >>>
    """
    itr = iter(itr)
    
    return _foldr(add, [], itr)

### concatMap
################################################################

def concatMap(func, itr):
    """
    concatMap(func, iterable) -> list
    
    concatMap is a composition of concat and map. Note that the `func`
    callable must return lists, not single values
    
    >>> def double(x_xs): return [x_xs[0], x_xs[0]]
    ...
    >>> concatMap(double, [[1], [2], [3]])
    [1, 1, 2, 2, 3, 3]
    >>>
    """
    if not callable(func):
        raise TypeError("First argument to concatMap must be callable")
    itr = iter(itr)
    
    return concat(map(func, itr))

### splitAt
################################################################

def splitAt(n, itr):
    """
    splitAt(n, iterable) -> (generator, generator)
    
    splitAt(n, iterable) == (take(n, iterable), drop(n, iterable))
    """
    return take(n, itr), drop(n, itr)
