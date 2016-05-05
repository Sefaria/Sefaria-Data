__author__ = 'stevenkaplan'
import pdb
#first generate 26*26 'words' made up of two letter combinations
#then retrieve the ID for each find which will be about 26*26*(2 through 5)
#then for each ID retrieve all related artists and of all related artists, their related artists
#then for each first degree related artist, iterate and increase the connection between the genre of
#original artist and related artist by 3.  then for each second degree related artist, iterate and
#increase the connection between the genre of original artist and related artist by 2.


def generateWords():
    strings = []
    for i in range(26):
      first_letter = chr(97+i)
      for j in range(26):
        strings.append(first_letter + chr(97+j))
    return strings


def generateArtists():



if __name__ == "__main__":
    words = generateWords()
    artists = generateArtists(words)