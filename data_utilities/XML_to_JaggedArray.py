'''
How to convert XML tree into JaggedArray
User gives a level of depth to go to and then xpath("string()") on that depth to return a jagged array of that depth. 
'''
import pdb
from lxml import etree

class XML_to_JaggedArray:


	def __init__(self, file, depth):
		#depth is level at which tree has text
		self.file = file
		xml_text = ""
		for line in open(self.file):
			xml_text += line
		self.root = etree.XML(xml_text)
		self.depth = depth



	def goDownToText(self, element, level):
		if level == self.depth:
			return element.xpath("string()").replace("\n\n", " ")
		else:
			text = []
			for child in element:
				result = self.goDownToText(child, level+1)
				text.append(result)
			return text





if __name__ == "__main__":
	parser = XML_to_JaggedArray("Robinson_MosesCordoveroIntroductionToKabbalah.xml", 2)
	print parser.root
	text = parser.goDownToText(parser.root, 0)
	pdb.set_trace()

