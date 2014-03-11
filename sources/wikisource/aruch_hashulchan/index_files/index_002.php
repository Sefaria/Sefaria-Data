var page_ns_prefixes= {
        'br':'Pajenn',
	'ca':'Pàgina',
	'de':'Seite',
	'el':'Σελίδα',
	'en':'Page',
        'eo':'Paĝo',
	'es':'Página',
        'fa':'برگه',
	'fr':'Page',
	'hr':'Stranica',
	'hu':'Oldal',
	'hy':'Էջ',
	'it':'Pagina',
	'la':'Pagina',
	'no':'Side',
	'pl':'Strona',
	'pt':'Página',
	'ru':'Страница',
	'sl':'Stran',
	'sv':'Sida',
        'vec':'Pagina',
	'vi':'Trang',
	'zh':'Page',
	'old':'Page',
	'oldwikisource':'Page'
}

if(!self.ws_messages) self.ws_messages = { }
function ws_msg(name) {
   var m = self.ws_messages[name];
   if(m) return m; else return name;
}


/* cross-domain transclusions through the API */

function get_url(lang, project) {
        if (!project) project = 'wikisource';
        if (lang == 'commons' || lang == 'species' || lang == 'meta') project = 'wikimedia';

	if (lang == "old" || lang == "oldwikisource") {
		return 'wikisource.org';
	} else {
		return lang + '.' + project + '.org';
	}
}

function api_url(lang, project) {
	return '//' + get_url(lang, project) + '/w/api.php';
}

/* transform all href from relative to absolute, so that they still point to the right place */
function absoluteLinks(text, lang, project) {
    if (!text) return '';
    return text
     .replace(/href="\/wiki\//g, 'href="//' + get_url(lang, project) + '/wiki/')
     .replace(/href="\/w\//g, 'href="//' + get_url(lang, project) + '/w/')
}

function iw_trans_callback(res){
	var target = res.requestid.replace(/___.*/i, "");
	var spans = jQuery('span.iwtrans');

	for (var i = 0; i<spans.length; i++) {
		var item = spans[i];

		var m = item.title.split("|");
		lang=m[0];
                project = 'wikisource'; //default
                if (m.length > 2) project = m[2];

		if (item.title == target) {
			$(item).html(absoluteLinks(res.parse.text['*'], lang, project));
		}
	}
}

function iw_trans() {
	var spans = jQuery( 'span.iwtrans' ) ;
	for(var i = 0; i<spans.length; i++) {
		var item = spans[i];
		var m = item.title.split("|");
		lang = m[0];
		title = m[1];
                project = 'wikisource'; //default
                if (m.length > 2) project = m[2];

		var url = api_url(lang, project) + '?format=json&requestid=' + item.title + "___" + Math.random() + '&action=parse&text={{:'+title+'}}<references/>&callback=iw_trans_callback&title='+title;
		importScriptURI(url);
	}
}
jQuery(document).ready(iw_trans);

function iw_pages_callback(res) {
	var target = res.requestid.replace(/___.*/i, "");
	var spans = jQuery('span');

	for(var i = 0; i<spans.length; i++) {
		var item = spans[i];
 
		var m = item.title.split("|");
		lang=m[0];
                project = 'wikisource'; //default

                var txt = absoluteLinks(res.parse.text['*'], lang, project);
  
		/* fix for it.wikisource */
		$txt = $('.SAL, .numeropagina', txt).remove().end();

		if( ($(item).hasClass("iwpages") || $(item).hasClass("iwpage")) && item.title == target ) {
			$(item).html($txt);
		}
	}
}

function iw_pages() {
        /* if(wgCanonicalNamespace != page_ns_prefixes[wgContentLanguage]) return; */

	var spans = jQuery( 'span.iwpages' ) ;
	for(var i = 0; i<spans.length; i++) {
		var item = spans[i];

		var m = item.title.split("|");
		lang = m[0];
		project = 'wikisource';
		title = m[1];
		from = m[2];
		to = m[3];
		fromsection = '';
		tosection = '';
		if (m.length > 4) fromsection = m[4];
		if (m.length > 5) tosection = m[5];
	        url = api_url(lang) + '?format=json&requestid=' + item.title + "___" + Math.random() + '&action=parse&callback=iw_pages_callback&text=<pages index="'+title+'" from='+from+' to='+to+' fromsection='+fromsection+' tosection='+tosection+' /><references/>&title='+title;
		importScriptURI(url);
	}
	var count = 0;
	var spans = jQuery( 'span.iwpage' ) ;
	for(var i = 0; i<spans.length; i++) {
		var item = spans[i];
		var m = item.title.split("|");
		lang = m[0];
		project = 'wikisource';
		count = count + 1;
		title = page_ns_prefixes[lang]+":"+m[1];
		if(m.length>2) section=m[2]; else section=false;
		if(section) section_title='lst\|'+title+'\|'+section; else section_title = title;
		url = api_url(lang) + '?format=json&requestid=' + item.title + "___" + Math.random() + '&action=parse&callback=iw_pages_callback&text={{'+section_title+'}}<references/>&title='+title;
		importScriptURI(url);
	}
	cs = document.getElementById("corr-info");
	if(cs && count) {
		if(count==1) {
			cs.innerHTML += ' ' + ws_msg('iwtrans') + ' <a href="//' + get_url(lang) + '/w/index.php?title='+title+'">' + get_url(lang) + '</a>.';
		} else {
			cs.innerHTML += ws_msg('iwtrans2');
		}
	}
}

jQuery(document).ready(iw_pages);