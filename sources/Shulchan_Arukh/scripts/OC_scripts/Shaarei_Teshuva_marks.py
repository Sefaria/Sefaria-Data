# encoding=utf-8

"""
Problem: Shaarei Teshuva uses the Be'er Hetev marks, but does not use all of them and has some of it's own.
Solution: Create unique marks for the Shaarei Teshuva

Step 1: Identify all locations where Be'er Hetev marks go out of order. Manually check if any of these are unique to
Shaarei Teshuva. If so - change the mark to the new Shaarei Teshuva mark. Keep a record of the locations where these
were added.

Step 2: Compare Be'er Hetev marks to the existing text on Sefaria. Any discrepancy should be checked against Shaarei
Teshuva. As before, any changes should be tracked.

Step 3: Parse Shaarei Teshuva and determine which Be'er Hetev markers need to have a Shaarei Teshuva marker added next
to them. Special care needs to be taken in places where a unique Shaarei Teshuva marker has already been added.
Three lists can be made for each siman:
    1) Available Be'er Hetev marks at which a Shaarei Teshuva mark can be added
    2) Shaarei Teshuva markers that are already there
    3) Shaarei Teshuva comments that need a marker
For each comment that needs a marker, I first check if the marker has already been set. If not, I can then look at the
available locations and set the appropriate marker. If no available locations exist, log the location and handle manually.
Once a location has been used to match, remove from the list of available matches.

Duplicates in a Shaarei Teshuva siman may cause a buggy edge case. Before deciding if this should be handled, it's probably
wise to determine how often that happens and what bugs might arise.

Shaarei Teshuva marked with @62
"""
