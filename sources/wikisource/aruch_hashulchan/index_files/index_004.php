/* הוספת כפתור טבלה, המעלה כלי ליצירת טבלאות */
/* גרסה 0.1, נלקח מוויקיפדיה בצרפתית, נכתב במקור על־ידי Dake */
function generateTableau( nbCol, nbRow, border, styleHeader, styleLine, styleSort ) {
    var code = "\n";
    if ( styleHeader ) {
        code += '{| class="wikitable';
        if(styleSort) code += ' sortable';
        if(border==1) code += '"\n';
        else code += '" border="' + border + '"\n';
    } else {
        code += '{| border="' + border + '"\n';
        code += "|+ כותרת הטבלה\n";
    }

    for( var i = 0; i < nbCol; i++) {
        if(i==0) code += "! כותרת " + i;
        else code += " !! כותרת " + i;
    }
    if(nbCol>0) code+="\n";
    for( var i = 0; i < nbRow; i++ ) {
        if( i %2 == 1 && styleLine ) {
            code += '|- style="background-color: #EFEFEF;"\n';
        } else {                
            code += "|-\n";
        }

        for( var j = 0; j < nbCol; j++ ) {
            if(j==0) code += "| תא " + i;
            else code += " || תא " + i;
        }
       if(nbCol>0) code+="\n";
    }

    code += "|}";
    insertTags( "", "", code );
}

function popupTableau() {
    var popup = window.open( "", "popup", "height=240,width=250" );


    popup.document.write('<html><head><title>פרמטרים לטבלה</title>');
    popup.document.write('<style type="text/css" media="screen,projection">/*<![CDATA[*/ @import "/skins-1.5/monobook/main.css"; @import "/skins-1.5/monobook/rtl.css"; /*]]>*/</style>');
    popup.document.write('<script type="text/javascript">function insertCode() {');
    popup.document.write('var row = parseInt( document.paramForm.inputRow.value ); ');
    popup.document.write('var col = parseInt( document.paramForm.inputCol.value ); ');
    popup.document.write('var bord = parseInt( document.paramForm.inputBorder.value ); ');
    popup.document.write('var styleHeader = document.paramForm.inputHeader.checked; ');
    popup.document.write('var styleLine = document.paramForm.inputLine.checked; ');
    popup.document.write('var styleSort = document.paramForm.sortedTable.checked; ');
    popup.document.write('window.opener.generateTableau( col, row, bord, styleHeader, styleLine, styleSort); ');
    popup.document.write('}</script>');
    popup.document.write('</head><body>');
    popup.document.write('<p>הזינו פרמטרים לטבלה : </p>');
    popup.document.write('<form name="paramForm">');
    popup.document.write('מספר שורות : <input type="text" name="inputRow" maxlength="3" value="3" style=\"width:50px;\"><p>');
    popup.document.write('מספר עמודות : <input type="text" name="inputCol" maxlength="3" value="3" style=\"width:50px;\"><p>');
    popup.document.write('רוחב מסגרת : <input type="text" name="inputBorder" maxlength="2" value="1" style=\"width:50px;\"><p>');
    popup.document.write('טבלה מעוצבת : <input type="checkbox" name="inputHeader" checked="1" ><p>');
    popup.document.write('שורות אפורות לסירוגין: <input type="checkbox" name="inputLine" checked="1" ><p>');
    popup.document.write('טבלה ממוינת: <input type="checkbox" name="sortedTable"><p>');
    popup.document.write('</form>');
    popup.document.write('<p><a href="javascript:insertCode(); self.close();"> הוספת הקוד לחלון העריכה</a></p>');
    popup.document.write('<p><a href="javascript:self.close()"> סגירה</a></p>');
    popup.document.write('</body></html>');
    popup.document.close();
}

/* הוספת כפתור טבלאות לסרגל הכלים */
function tableButton() {
	if( document.getElementById("toolbar") ) {
		var tableButton = document.createElement("img");
		tableButton.width = 23;
		tableButton.height = 22;
		tableButton.src = "//upload.wikimedia.org/wikipedia/commons/6/60/Button_insert_table.png";
		tableButton.border = 0;
		tableButton.alt = "הוספת טבלה";
		tableButton.title = "הוספת טבלה";
		tableButton.style.cursor = "pointer";
		tableButton.onclick = popupTableau;
		var lastChild = document.getElementById("toolbar").lastChild;
		if (lastChild && lastChild.id == "templatesList") 
			document.getElementById("toolbar").insertBefore(tableButton, lastChild);
		else 
			document.getElementById("toolbar").appendChild(tableButton);
	}
}

hookEvent("load", tableButton);