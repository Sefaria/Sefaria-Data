var page_ns_prefixes= { 
        'be':'Старонка',
        'be-tarask':'Старонка',
	'br':'Pajenn',
	'ca':'Pàgina',
	'de':'Seite',
	'en':'Page',
        'eo':'Paĝo',
	'es':'Página',
	'fr':'Page', 
	'hr':'Stranica',
	'hu':'Oldal',
	'hy':'Էջ',
	'it':'Pagina',
	'la':'Pagina',
        'ml':'താൾ',
        'mr':'पान',
	'no':'Side',
	'pl':'Strona',
	'pt':'Página',
	'sl':'Stran',
	'sv':'Sida',
	'ru':'Страница',
        'te':'పుట',
	'vi':'Trang',
	'vec':'Pagina',
	'zh':'Page'
}

var index_ns_prefixes= { 
        'be':'Індэкс',
        'be-tarask':'Індэкс',
	'br':'Meneger',
        'ca':'Llibre',
	'de':'Index',
	'en':'Index',
        'eo':'Indekso',
	'es':'Índice',
	'fr':'Livre',
	'hy':'Ինդեքս',
	'it':'Indice',
	'la':'Liber',
        'ml':'സൂചിക',
        'mr':'अनुक्रमणिका',
	'no':'Indeks',
	'pt':'Galeria',
	'sv':'Index',
	'ru':'Индекс',
        'te':'సూచిక',
	'vec':'Indice',
        'vi':'Mục_lục'
}

/* messages to be moved 
 'it':'Il testo proviene da', 
 'la':'Hic textus visibils est in', 
 'es':'Su texto procede de', 
 'ca':'El seu text procedeix de' 
*/


if(!self.ws_messages) self.ws_messages = { }

function ws_msg(name) {
   var m = self.ws_messages[name];
   if(m) return m; else return name;
}

/* Note : there is a similar function in wikibits.js, but it does not work for me on page numbers */
function get_elements_by_classname(classname, tagname) {
	if(document.getElementsByClassName) return document.getElementsByClassName(classname);
	var ml = new Array();
	var l = document.getElementsByTagName(tagname);
	for (var i=0; i< l.length; i++) {
		var a = l[i]; 
		if( a.className.indexOf(classname) !=-1 ) ml[ml.length] = l[i];
	}
	return ml;
}
        

function get_optlist() {
	var optlist = document.getElementById("optlist");
	if(!optlist) {
		var displayOptions = document.createElement("div");
                if (self.skin=='vector') displayOptions.className = "portal collapsed"; else displayOptions.className = "portlet";
		if (self.skin=='vector') cl="body"; else cl="pBody";
		displayOptions.innerHTML = '<h3>' + ws_msg('optlist') + '<\/h3><div class="'+cl+'"><ul id="optlist"></ul><\/div>';
                var ptb = document.getElementById("p-tb");
                ptb.parentNode.insertBefore(displayOptions,ptb);
                displayOptions.setAttribute("id","p-displayOptions");
                displayOptions.id="p-displayOptions"; /* */
		optlist = document.getElementById("optlist");
	}
	return optlist;
}


/*** Cookies (depreciated, use jQuery.cookie) ***/

function SetCookie(name,value) {
	jQuery.cookie(name, value);
}
  
function GetCookie(name) {
	return jQuery.cookie(name);
}


/**** Display options ****/

function OptionText() {
   var indexNavigationBar = 0;
   // iterate over all < span >-elements until class "OptionText" is found
   for(
           var i=0; 
           SpanElem = document.getElementsByTagName("span")[i]; 
           i++
       ) {
       // if found an option span
       if (SpanElem.className == "OptionText") {
          //SpanElem.style.display = 'none';
          OptionTitle = SpanElem.title;
          OptionStyle = SpanElem.firstChild.getAttribute('style');

          //check if option was already encountered...
          if(!document.getElementById(OptionTitle)){

            //read cookie
            var DisplayOptionDefault = true;
            CookieDisplayOption = jQuery.cookie("Display"+OptionTitle)
            if (CookieDisplayOption ) {
            if (CookieDisplayOption == "false") DisplayOptionDefault = false; }

            var PageDisplay = document.createElement("li");
            PageDisplay.setAttribute('id', OptionTitle);
            var PageDisplayLink = document.createElement("a");

            OptionText = document.createTextNode("Désactiver "+OptionTitle);
            PageDisplayLink.appendChild(OptionText);
            PageDisplayLink.setAttribute('href','javascript:void(0)');
            jQuery(PageDisplayLink).click(function() {
                        displayOptionText(OptionTitle, OptionStyle, DisplayOptionDefault);
            });
            PageDisplay.appendChild(PageDisplayLink);

            var optlist = get_optlist();
            optlist.appendChild(PageDisplay);

            displayOptionText(OptionTitle,OptionStyle,DisplayOptionDefault);
          }
       }
   }
 }

 function displayOptionText(optiontitle, optionstyle, bool) {
  
  jQuery.cookie("Display"+optiontitle,bool);
  if( ! document.getElementById(optiontitle) ) return;
  var PageDisplayLink =  document.getElementById(optiontitle).firstChild;

   // iterate over all < span >-elements
   for(
           var i=0; 
           SpanElem = document.getElementsByTagName("span")[i]; 
           i++
       ) {
        // if found an option text
        if ((SpanElem.className == "OptionText") && (SpanElem.title == optiontitle)) {
          if(bool) {
            SpanElem.setAttribute('style',optionstyle);
            PageDisplayLink.firstChild.data = (optiontitle);
            PageDisplayLink.setAttribute('href', 'javascript:void(0)');
            jQuery(PageDisplayLink).unbind('click');
            jQuery(PageDisplayLink).click(function() {
                        displayOptionText(optiontitle, optionstyle, false);
            });
          }
          else {
            SpanElem.setAttribute('style','null');
            PageDisplayLink.firstChild.data = (optiontitle);
            PageDisplayLink.setAttribute('href', 'javascript:void(0)');
            jQuery(PageDisplayLink).unbind('click');
            jQuery(PageDisplayLink).click(function() {
                        displayOptionText(optiontitle, optionstyle, true);
            });

         }        
      }
   }
 }

$(document).ready( OptionText );

function restore_lst(){
        var editbox = document.getElementById('wpTextbox1');
        var search = /##[\s]*(.*?)[\s]*##[\s]*\n/;
        var a = editbox.value.split(search);
        var s = a[0]; 
        var ok = true;
        var m = parseInt(a.length/2);
        for( var i = 0 ; i < m ; i++ ) {
            var title = a[i*2+1];
            // Ensure we'll don't get twice quote.
            title = title.replace(/^"(.*)"$/, "$1");
            title = title.replace(/^'(.*)'$/, "$1");
            var content = a[i*2+2]; 
            if( title && content.substring(0,2)=='{|' ) content = '\n' + content;
            if(title) s = s + '<section begin="'+title+'"/>' + content + '<section end="'+title+'"/>\n';
            else s = s + content;
            /* if( i < m-1 ) s = s + "----\n"; */
        }
        editbox.value = s; 
}
 
/*
 * easy lst : hide section markers
 */
function easy_lst() {
        var editbox = document.getElementById('wpTextbox1');
        if(editbox) {

	var search = /<section\sbegin=[\s]*(.*?)[\s]*\/>/;
        var a = editbox.value.split(search);
        var s = a[0]; 
        var ok = true;
        for( var i = 0 ; i < parseInt(a.length/2) ; i++ ) {
            var title = a[i*2+1];
            var content = a[i*2+2]; 
            var r2 = /^([\s\S]*?)<section\send=(.*?)\/>(\n|)[\s]*([\s\S]*?)$/;
            var m2 = content.match(r2);
            if( m2 ) {
               title = title.replace(/^"(.*)"$/, "$1");
               title = title.replace(/^'(.*)'$/, "$1");
               if(s && s.charAt(s.length-1)!='\n' && s.charAt(s.length-1)!='|' ) s = s+'\n';
               s = s + "## " + title + " ##\n"+ m2[1] ;
               if( m2[4] ) { 
                  if( m2[4]!='----\n' ) {
                    if(s && s.charAt(s.length-1)!='\n' ) s = s+'\n';
                    s = s + "####\n" + m2[4] ;
                  } 
               }
             } else { 
               ok = false; /* alert("error"+title);*/
             }
        }
	if(ok) { 
             editbox.value = s; 
        } 
	var saveButton = document.getElementById("wpSave"); 
	var previewButton = document.getElementById("wpPreview"); 
	var diffButton = document.getElementById("wpDiff");
	if(saveButton){
                saveButton.onclick = restore_lst;
		previewButton.onclick = restore_lst;
		diffButton.onclick = restore_lst;
        }
   }
}

function easy_lst_setup() {
        if (self.proofreadpage_raw_lst || mw.config.get( 'wgCanonicalNamespace' ) !== 'Page')
            return;

        if ($.inArray(mw.config.get('wgAction'), ['edit', 'submit']) !== -1) {
            mw.loader.using('ext.proofreadpage.page', function () {
            // mimic code in the extension, there is a conditionnal deps on ext.wikiEditor.toolbar.
            if (mw.user.options.get('usebetatoolbar') && jQuery.inArray('ext.wikiEditor.toolbar', mw.loader.getModuleNames()) > -1) {
                mw.loader.using('ext.wikiEditor.toolbar', function() {
                   easy_lst();
                });
            } else {
                easy_lst();
            }
        });
    }
}


$(document).ready( easy_lst_setup );

/* fix to reposition running headers */
function pr_fix_page_headers(){
  if (mw.config.get( 'wgCanonicalNamespace' ) === 'Page' && $.inArray(mw.config.get('wgAction'), ['edit', 'submit']) !== -1) {
        var a = document.getElementById("pageheader"); 
	if (a) {
	    var p = a.parentNode;
            p.removeChild(a);
            p.parentNode.insertBefore(a,p);
	}
  }
}
$(document).ready( pr_fix_page_headers );