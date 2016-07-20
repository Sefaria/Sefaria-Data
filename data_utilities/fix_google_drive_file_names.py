import os
import glob
import pdb
for filename in os.listdir("."):
	if filename.find(".txt") != filename.rfind(".txt"):
		new_name = filename[0:-4]
		os.rename(filename, new_name)
