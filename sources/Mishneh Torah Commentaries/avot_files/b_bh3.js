	
var EnableDump = false;
var		Explorer = 2;		// unknown
var		GlobalLevel = 1;
var		dump = "";
var		BackText ="חזור אחורה";
var		BackLink = "";
var		IndexLinesCount = 0;
var		WellcomeText = "כמה מילים על האתר ...";
var		FixedWidth = ((location.search) != "?dyn"); // www.xxxxxx.index.html?pirsum.html => pirsum.html
 
function IsExplorer()
{
	if (Explorer == 2)
	{
		if (navigator.appName.indexOf("Microsoft") != -1)
			Explorer=1;
		else
			Explorer=0;
	}

	return (Explorer);
}


function WriteToFile(text, file) 
{
	// write to file    
	var fso = new ActiveXObject("Scripting.FileSystemObject");
	var s = fso.CreateTextFile(file, true);
    s.writeline(text);
    s.Close();
 }

function	start_dump()
{
	dump = "";
	EnableDump = 1;
}

function	stop_dump()
{
	EnableDump = 0;
//	alert (dump);

	WriteToFile (dump, "c:\\_JavaDump.txt");
}

function WriteCommand (value)
{
	document.write (value);
	
	if (EnableDump)
		dump += value + "\r\n";
}

function Print (text)
{
WriteCommand(text);
}


function print (text)
{
Print(text);
}


function PrintSearchGoogle (AdditionalText)
{
	print ("<form method='get' action='http://www.google.com/search' style='margin:0px; padding:0px; border:0; border-color:black; background-color:RGB(0,54,117);'>");

//	print ("<div style='padding:0px; margin:0px; border-size:2px; border-color:red;'>");	
	
	print ("<table border='0' padding='0' margin='0' cellpadding='10' width=100%>");

	print ("<tr><td width=100%; style='padding-top:10; padding-bottom:0; text-alignement:middle; background-color:RGB(0,54,117); color:white;'>");

	if (SearchBaseForGoogle != undefined && SearchBaseForGoogle != "")	
	{
		if (!IsExplorer())
			print ("<input type='submit' value='חפש'/ style='background-color:RGB(0,128,255); color:black; border-style:none; height:20px;'>");
		else
			print ("<input type='submit' value='חפש'/ style='background-color:RGB(0,128,255); color:black; border-style:none; height-top:0px; height:20px;'>");	

		print ("<input type='text'  name='q' size='20' maxlength='255' DIR='RTL' value=''  style='background-color:RGB(0,85,170); border-style:none;  color:white; height:20px;'>");
	}
	else
	{
		print ("&nbsp");
	
	}
		
	if (AdditionalText != undefined && AdditionalText != "")
	{
		print ("&nbsp&nbsp");
		print (AdditionalText);
	}
	print ("</td></tr>");
	print ("<tr>");
	print ("<td align='center' style='font-size:75%'>");
	print ("<input type='hidden' align='right' name='sitesearch' size='10' value='" + SearchBaseForGoogle + "' checked />");
	print ("<input id=lgr type=hidden name=meta value='lr=lang_iw'  checked>");
	print ("</td></tr>");

//	print ("<tr style='height:2px;' ><td width=100%; style='height:2px; line-height:2px; padding-top:10; padding-bottom:0; text-alignement:middle; dbackground-color:RGB(0,54,117); color:white;'>dddddd</td></tr>");		
	

	print ("</table>");
//	print ("</div>");
	print ("</form>");

}
/*
function begin (title)
{
	var	width = 750;

	print ("<html><head>");
	print ("<meta content='text/html'; charset=windows-1255' http-equiv='content-type'>");
	print ("<title>");
	print (title);
	print ("</title>");
	print ("<html>");
	print ("<body style=\"background-color:RGB(230,230,230); padding:20px; margin=0px; \">");

	print ("<center><div style='background-image: url(background.png); background-repeat: repeat-x; text-align:right; padding:22px; margin=0px; width:" + width + "px; background-color:RGB(255,255,250); border-width: 1px;border-style:solid; '>");

	print ("<BR><BR><BR><BR><BR><BR>")

	print ("<center>")
	PrintSearchGoogle();
	print ("</center>")
}
*/

function	PrintLeftSideOnGrayLine ()
{



}

function begin (title, name1, link1, name2, link2, name3, link3, name4, link4)
{
	FixedWidth = ((location.search) != "?dyn"); // www.xxxxxx.index.html?pirsum.html => pirsum.html

	var		width = (FixedWidth) ? GlobalWidth +"px" : "100%";
	var		names = new Array();	
	var		links = new Array();	
	var		size = 1;

	names[0] = "דף הבית";
	links[0] = Homepage;
	
	if (link4 != undefined)
		size=5;
	else if (link3 != undefined)
		size=4;
	else if (link2 != undefined)
		size=3;
	else if (link1 != undefined)
		size=2;
	
	names[1] = name1;
	names[2] = name2;
	names[3] = name3;
	names[4] = name4;
	
	links[1] = link1;
	links[2] = link2;
	links[3] = link3;
	links[4] = link4;
	
	var		temp = "";
	
	var		align = "top";
	
	if (IsExplorer())
		align = "middle";
	
	for (x=0; x<size; x++)
	{
//		<img style="width: 28px; height: 20px;" alt="" src="../Pics/btn_open.PNG" align="middle">
		var color = "RGB(196,234,255)";
		var	bmp = "c_home.png";
		
		if (x > 0)
			bmp = "c_arrow.png";
		
		if (x == size-1)
			color = "white";
		
		temp += "<a href='" + links[x] + "' style='color:" + color + "; text-decoration:none;'>";

		var	PicSize = 24;

		if (size > 4)
			PicSize = 20;		
		
		if (size > 1)
			BackLink = 	links[size-2];

		temp += "<img style=\"width:" + PicSize + "px; height:" + PicSize + "px; border-width:0;  align:" + align + "; \" align='" + align + "' src='" + bmp + "'> ";
		temp += names[x];
		temp += "</a>&nbsp&nbsp&nbsp";
	}

	var		LinksFontSize = 14;

	if (size > 4)
		LinksFontSize = 13;
	
	GlobalLevel = size;
	
	var		TreeLinks =	"<b style='font-size:" + LinksFontSize + "px; font-family:arial;'> " + temp + "</b>"; 
	
	print ("<html>");

	print ("<head>");	// this <head> working only on internet explorer
//		print ("<meta content='text/html'; charset='windows-1255' http-equiv='content-type'>");
//		print ("<meta http-equiv=Content-Type content='text/html; charset=windows-1255'>");
//		print ("<meta http-equiv=Content-Type content='text/html; charset=windows-1255'>");
	print ("</head>");
	
	print ("<style type='text/css'>");
		print ("#tab1,#tbody	{width:" + width +"; background-color:white; text-align: center; border:2; border-color:black; border-style:solid; border-width:1px; border-color:grey; cellpadding:0; cellspacing:0; }");
		if (FixedWidth)
			print ("#td1	{background-color: RGB(0,0,135); height: 100px; background-image: url(c_background.png); background-repeat: repeat-x; color:white; border-style:none; border:0;}");
		else
			print ("#td1	{background-color: RGB(0,0,135); height: 10px;  background-repeat: repeat-x; color:white; border-style:none; border:0;}");

	print ("</style>");

	print ("<title>");
		print (title);
	print ("</title>");

	print ("<body style=\"background-color:RGB(173,206,255); padding:" + ((FixedWidth) ? "20px" : "0px") + "; margin=0px; \">");

	print ("<center>");
	print ("<table id='tab1' style='color: black;  direction:rtl; text-align:right' border='0'  cellpadding='0' cellspacing='0' marginheight='0' marginwidth='0' margin='0'>");
	print ("<tbody style='valign:top;' >");

	print ("<tr id='tr1' style='dir:rtl; valign:top;' >	");
	print ("<td id='td1' style='text-align: left; font-size:12px; font-family:arial; padding-left:0px; padding-top:6px;' valign='top' >");

	if (SearchBaseForGoogle != undefined && SearchBaseForGoogle != "")
	{
		print ("<b><a href='http://www.ateret4u.com' style='color:RGB(124,172,255);'>ישיבת עטרת חכמים</a></b>");
		print ("&nbsp &nbsp");
		print ("<b><a href='http://www.toratemetfreeware.com/Downloads.htm' style='color:RGB(124,172,255);'>להורדת המאגר</a></b>");
		print ("&nbsp&nbsp&nbsp &nbsp&nbsp");
	}
	else
	{
		print ("<b></b>");
		print ("&nbsp &nbsp");
		print ("<b></b>");
		print ("&nbsp&nbsp&nbsp &nbsp&nbsp");
	}
		
	if (!FixedWidth)
		print ("<center style='font-size:35px; text-decoration:none; '>תורת אמת - <small><small>ONLINE</small></small></center>");
	
	print ("</td>");
	print ("<tr>");
	print ("<td height=10px style='margin:0; padding-right:0; '>");	
//	print (TreeLinks);
	PrintSearchGoogle(TreeLinks);
	print ("</td></tr>");

//	if (FixedWidth)		// draw grey line only on fixed with because problem on Chrome !!!
	{
		print ("<tr style='background-color:RGB(192,192,192); padding:0px; padding-right:8px; margin:0; padding-top:0px; padding-bottom:0px; '>");
		print ("<td>");

		print ("<table style='padding:0px; margin:0px; '><tbody><tr style='text-alignement:middle;'>");
			print ("<td>");
				if (size > 1)
				{
					print ("<a href='" + BackLink + location.search + "'  style='text-decoration:none; border-style:none; border-size:10px;' >");
					print ("<img src='c_back2.png'  style='border-style:none; margin:0px; padding:0px;'>");
					print ("</a>");
				}
				else
				{
					print ("<img src='c_back3.png'  style='border-style:none; margin:0px; padding:0px;'>");
				}
			print ("</td>");
			
			print ("<td width=100% style='direction:ltr;  padding:0px; margin:0px; padding-left:8px; text-alignement:middle;'>");

				if (FixedWidth)	
				{
					print ("<a href='a_root.html?dyn' style='text-decoration:none; padding:0px;'>");
					print ("<img src='c_nerrow.png'  style='border-style:none; margin:0px; padding:0px; '>");		
					print ("</a>");
				}
				else
				{
					print ("<a href='a_root.html' style='text-decoration:none;'>");
					print ("<img src='c_wide.png'  style='border-style:none; margin:0px; padding:0px;'>");											
					print ("</a>");
				}

			if (FixedWidth)	
			{
				print ("<a href='a_rights.html" + location.search + "' style='padding:0px; margin:0px; color:blue; font-family:arial;'>");
				print ("<img src='c_rights.png'  style='border-style:none; border-size:0px; margin:0px; padding:0px; '>");					
				print ("</a>");			
			}
			else
			{
				print ("<a href='a_rights.html" + location.search + "' style='text-alignement:bottom; padding:0px; margin:0px; color:blue; font-family:arial; font-size:13px; text-alignement:middle;'>");
				print ("<b>כל הזכויות שמורות - לפרטים לחץ כאן</b>");
				print ("</a>");			
			}
			

			print ("</td>");				
				
		print ("</td></tr></tbody></table>");		
		

		
		print ("</td>");
		print ("</tr>");
	}
	
	print ("<tr><td style='padding:" +  ((FixedWidth) ? "32px" : "10px") + ";'>");

}



// #rep3={=<div style='ffont-size:100%;  padding:15; margin:0;  border-width: 2px;border-style:solid; border-color=MIX1;background-color=MIX2; color=MIX3;' >^^}=</div>

function end ()
{
for (x=0; x<100; x++) print ("<BR>");
//print("</div>");
print ("</td></tr></tbody></table>");
print ("</body></head></html>");
}


function	BeginIndex (NumOfLines)
{
//	print ("<br><BR>");

	print ("<div style='padding:32px; padding-top:0px; '>");
	
	if (BackLink == "")		// if ROOT (indirect indication)
		AddIndex (WellcomeText, "a_wellcome.html", 3);
	print ("<br>");



}

function	AddIndex (Name, Link, Type)
{
	Link += location.search;
	var		align = "top";
//	alert(Link);
	//if (IsExplorer())
	align = "bottom";
	var		bmp = "c_folder.png";
	var		LineHeightControl = "";
	
	if (Name == WellcomeText)
		bmp = "c_lev.png"
	else if (Name == BackText)
		bmp = "c_back.png"
	else
		bmp = "c_" + Type + ".png";
/*
	else if (Type == 1)
		bmp = "c_book.png";
	else if (Type == 2)
		bmp = "c_splited_book.png";
	else if (Type == 3)
		bmp = "c_all_book.png";
*/		

	var		PicSize = 20;
	var		image = "<img style=\"width:" + PicSize + "px; height:" + PicSize + "px; border-width:0;  align:" + align + "; \" align='" + align + "' src='" + bmp + "'> ";
	var		color = "RGB(12,79,149)"; 
	var		size = "28";
	
	if (Name == WellcomeText)
	{
		color = "RGB(50,180,255)";
		size = "22";
		LineHeightControl = "line-height:10px; ";
	}
	
	if (Name.indexOf("כל הספר") != -1)
	{
		color = "grey";
		size = "22";
		LineHeightControl = "line-height:10px; ";
		print ("<br>");
	}	
	
//	print ("&nbsp&nbsp&nbsp&nbsp <a href='" + Link + "' style='font-size:" + size + "px; color:" + color + "; text-decoration:none; " + LineHeightControl + "'>" + image +  Name + "</a><br>");
	print ("<a href='" + Link + "' style='font-size:" + size + "px; color:" + color + "; text-decoration:none; " + LineHeightControl + "'>" + image +  Name + "</a><br>");
	
	IndexLinesCount++;
}

function	EndIndex ()
{
	while (IndexLinesCount < 40)
	{
		IndexLinesCount++;
		print ("<br>\n");
	}

	print ("</div>");
}


