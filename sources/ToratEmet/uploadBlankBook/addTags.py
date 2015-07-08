import re

def addTag(text, inSym, inHTML, outSym, outHTML, keepTrack): #maybe add something for first appearance of sym (like <br>)
	if not (hasattr(addTag, "stored")):
		addTag.stored = dict()  # it doesn't exist yet, so initialize it (first call to function)
	
	if inSym not in addTag.stored:
		addTag.stored[inSym] = 0

	if(keepTrack):##update the total amount of these thing
		newValue = addTag.stored[inSym] + text.count(inSym) - text.count(outSym)
	
	for i in range(addTag.stored[inSym]): #there is still a smallBox from the previous call
		text = inHTML + text
		
	if(keepTrack):##update the total amount of these thing
		addTag.stored[inSym] = newValue

	text = text.replace(inSym, inHTML).replace(outSym,outHTML)
		
	for i in range(addTag.stored[inSym]): #close the smallBox from previous call
		text += outHTML
		
	if(addTag.stored[inSym] < 0):#something went wrong...
		user = 'continue'
		while(user != 'n'):
			user = input(str(addTag.stored) + "\n" + inSym + " is at " + str(addTag.stored[inSym]) + ".\ny for restoring back to 0.\n'c' to clear everything.\n'n' for ignore.\n\n") 
			if user == 'y':
				addTag.stored[inSym] = 0
				break
			elif user == 'c':
				addTag.stored = dict()
				break
	if(('{' in addTag.stored) and addTag.stored['{'] >0):
		x = input("the { is being used")
		
	
	
	return text

def addTags(text, keepTrack):

	#replace their font things with normal html tags.
	text = addTag(text,"[[[[[[", "<big><b>", "]]]]]]", "</b></big>", keepTrack)
	text = addTag(text,"[[[[[", "<big>",  "]]]]]", "</big>", keepTrack)
	text = addTag(text, "[[[[", "<small>", "]]]]", "</small>", keepTrack)
	text = addTag(text, "[[[", "<b>", "]]]", "</b>", keepTrack)
	text = addTag(text, "[[", "<b>", "]]", "</b>", False)
	text = addTag(text, "(((", "<small>", ")))", "</small>", keepTrack)
	text = addTag(text, "((", "<small>", "))", "</small>", False)
	text = addTag(text, "{{{{", "<small>", "}}}}", "</small>", keepTrack)
	text = addTag(text, "{{", "<small>", "}}", "</small>", keepTrack)
	#text = re.sub('\s\{.{1,3}\}', "", text) #can be used to replace {number}
	text = addTag(text, "{", "<small>", "}", "</small>", False)
	text = addTag(text, "(", "<small>(", ")", ")</small>", False)
	
	

	
	return text;
	