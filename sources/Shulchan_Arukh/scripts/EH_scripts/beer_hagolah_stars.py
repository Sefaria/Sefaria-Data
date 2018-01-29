# coding=utf-8

"""
Map out stars in Mechaber text to Beer HaGolah

1) Identify locations in Beer HaGolah file where stars appear:
{
    siman_num,
    preceding_index: number of preceding beer hagolah comment,
    preceding_letter: letter of preceding beer hagolah comment,
    following_index
    following_letter
}

2) Instantiate a StructuredDocument around the Shulchan Arukh files

3) Use the StructuredDocument to find stars based on the identifying data. Check that only a single star exists
in the desired location

"""
