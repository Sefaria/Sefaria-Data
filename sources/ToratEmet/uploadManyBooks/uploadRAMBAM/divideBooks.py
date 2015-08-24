
def divideBook(filename, outpath):
	file = open(filename, 'r');
	
	booksList = open(outpath + 'booksList.txt', 'w');
	lines = file.readlines();

	bookCount =0
	output = open(outpath + 'dummy.txt', 'w');
	for line in lines:
		if(line.find('#') ==0): #start new books
			output.close()
			newFileName = outpath + str(bookCount) + ".txt"
			output = open(newFileName, 'w') 
			output.write('\n\n\n\n')
			booksList.write(newFileName + "$$$$" + line[2:]) #.replace(" ","_")
			bookCount = bookCount +1
			
		else:
			output.write(line)
			
filename = '90002_מדע.txt';
divideBook('files/' + filename, 'divided/' + 'madda' + '_')