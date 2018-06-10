init_4gen = function () {
  var $;

  if (typeof jQuery !== 'undefined') {
    $ = jQuery;
  }


  /*jslint browser: true, regexp: false */
  /*global Effect, jQuery, $,Element, escape */

  // CHANGEME
  var defaultViewManager = 'scroll';
  var adjacentLoadPages = 3;
  var adjacentFontLoadPages = 8;
  var ie6_pngfix_shim = '/images/4gen/trans_1x1.gif';
  var pagePadding = 30.0; // The padding on each page. (margin, padding, shadows, etc.)
                          // We may need to break this into width-wise and height-wise at some point.
  var extrasWidth = 315.0;

  var fontLoaderStrategy;
  var FONT_LOADER_EOT = 1;
  var FONT_LOADER_CSS_TTF = 2;
  var FONT_LOADER_MULTI_SVG = 3;

  var FONT_SERV_VERSION = 12; // Just change it when font serv changes.  just a cache buster

  /*******************************************************************************************

    HTML Page Resizer

  *******************************************************************************************/

  if (!window.console) {
    window.console = {log:function () {}};
  }

  // We only care about the DocumentManager in this
  var DocumentManager = (function () {

      //  Base64 encode / decode
      //  http://www.webtoolkit.info/

      var Base64 = {

        // private property
        _keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",

        // public method for decoding
        decode : function (input) {
          var output = "";
          var chr1, chr2, chr3;
          var enc1, enc2, enc3, enc4;
          var i = 0;

          input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

          while (i < input.length) {

            enc1 = this._keyStr.indexOf(input.charAt(i++));
            enc2 = this._keyStr.indexOf(input.charAt(i++));
            enc3 = this._keyStr.indexOf(input.charAt(i++));
            enc4 = this._keyStr.indexOf(input.charAt(i++));

            chr1 = (enc1 << 2) | (enc2 >> 4);
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
            chr3 = ((enc3 & 3) << 6) | enc4;

            output = output + String.fromCharCode(chr1);

            if (enc3 != 64) {
              output = output + String.fromCharCode(chr2);
            }
            if (enc4 != 64) {
              output = output + String.fromCharCode(chr3);
            }

          }

          output = Base64._utf8_decode(output);

          return output;

        },

        // private method for UTF-8 decoding
        _utf8_decode : function (utftext) {
          var string = "";
          var i = 0;
          var c = 0;
          var c1 = 0;
          var c2 = 0;
          while ( i < utftext.length ) {

            c = utftext.charCodeAt(i);

            if (c < 128) {
              string += String.fromCharCode(c);
              i++;
            }
            else if((c > 191) && (c < 224)) {
              c2 = utftext.charCodeAt(i+1);
              string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
              i += 2;
            }
            else {
              c2 = utftext.charCodeAt(i+1);
              c3 = utftext.charCodeAt(i+2);
              string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
              i += 3;
            }

          }

          return string;
        }

      };

      // addEventHelper takes the owner OBJ which will be "this"
      // when the callbacks are called, and the names of possible events
      //
      // It adds the methdos (addEvent, removeEvent, and fireEvent) to
      // the ownerObj
      //
      // Just use it like
      // addEventHelper(cls, ['resize', 'cheeseup', 'lolcats']); after you declare your class
      // and call this.initEventHelper in your constructor
      //
      // change eventListenerEnabled to suppress events from firing

      // A helper class to make it easy for our classes to have callbacks
      function EventHelper (possibleEvents) {
      }

      EventHelper.prototype.initEventHelper = function () {
        this.eventListenerEnabled = true;
        this.eventListeners = {};
        for (var i = 0; i < this.possibleEvents.length; i++) {
          this.eventListeners[this.possibleEvents[i]] = {};
        }
      };

      // To ensure that callbacks with the function text but different
      // contexts can be registered, callbacks are index by a unique identifier
      // which is attached to the function as ._uid
      EventHelper.prototype.addEvent = function(eventName, callback) {
        if (!this.eventListeners[eventName]) {
          throw eventName + " is not a valid type of event";
        }
        // Initialize the uid counter if need be
        if (!this.eventListeners[eventName].next_uid) {
          this.eventListeners[eventName].next_uid = 1;
        }
        // Assign the uid and increment
        if(!callback._event_listener_uid) {
          callback._event_listener_uid = this.eventListeners[eventName].next_uid;
          this.eventListeners[eventName].next_uid++;
        }
        this.eventListeners[eventName][callback._event_listener_uid] = callback;
      };

      // Only delete the same instance of callback that was based into
      // add event
      EventHelper.prototype.removeEvent = function(eventName, callback) {
        delete this.eventListeners[eventName][callback._event_listener_uid];
      };


      // Fires all the eventListeners for an event name
      EventHelper.prototype.fireEvent = function(eventName, arg1/*, ...*/) {
        if (!this.eventListenerEnabled) {
          return;
        }

        var eventsToFire = this.eventListeners[eventName];
        // pop off the eventName
        var newArgs = [];
        if (arguments.length > 1) {
          newArgs[arguments.length - 2] = null;
          //make new array without the first arg
          for (var i = 1; i < arguments.length; i++) {
            newArgs[i-1] = arguments[i];
          }
        }

        var self = this;
        function startFireEvent(func) {
          // Have it call the function in a new thread
          //window.setTimeout(function () {
              func.apply(self, newArgs);
          //  },
          //  0);
        }
        for (var c in eventsToFire) {
          if (c != 'next_uid' && eventsToFire.hasOwnProperty(c)) { //Prevent next_uid from being called as a function WAT
            startFireEvent(eventsToFire[c]);
          }
        }
      };


      // Some ghetto inheritance
      // make sure you cann eventHelper constructors
      function addEventHelper(cls, possibleEvents) {
        cls.prototype.addEvent = EventHelper.prototype.addEvent;
        cls.prototype.removeEvent = EventHelper.prototype.removeEvent;
        cls.prototype.fireEvent = EventHelper.prototype.fireEvent;
        cls.prototype.initEventHelper = EventHelper.prototype.initEventHelper;

        cls.prototype.possibleEvents = possibleEvents;
      }


      /////////////////
      // Font Loader declarations
      //////////////////////

      //////////////////////////////////////////////
      //
      // Some Constants used for FontLoader
      //
      //////////////////////////////////////////////
      var FONT_PRELOAD_BED_ID = 'font_preload_bed';
      var STUB_CHAR = "\uF8FF";

      // Used for styles
      var isIe = function () {
        return !document.styleSheets[0].insertRule;
      };

      var isInt = function(i) {
        return i % 1 == 0;
      };

      var set_href = function(a, href) {
          if(isIe()) {
              /* IE changes the text of a link once the href is changed by js if
                 the link text looks like a link as well (e.g. if it starts with "www".)
                 The following makes sure the link text stays unchanged.
               */
              var text = a.innerHTML;
              a.href = href;
              if(a.innerHTML != text)
                  a.innerHTML = text;
          } else {
              a.href = href;
          }
      };

      var isFroYo = (function () {
          var uagent = navigator.userAgent.toLowerCase();
          return uagent.search("android 2.2") > -1; // Special check for froyo
        })();

      var isMobileSafari = (function () {
          var uagent = navigator.userAgent.toLowerCase();
          return (uagent.search("mobile") > -1 &&
            uagent.search("safari") > -1 &&
            !isFroYo); // Special check for froyo
        })();

      var isWebKit = navigator.userAgent.indexOf('AppleWebKit/') > -1;



      fontLoaderStrategy = (function () {
          if (isIe()) {
            return FONT_LOADER_EOT;
          } else if (isMobileSafari) {
            return FONT_LOADER_CSS_TTF;
          } else {
            return FONT_LOADER_CSS_TTF;
          }
        })();

      // Kludge for IE  Make it less aggressive for loading fonts
      if (isIe()) {
        adjacentFontLoadPages = 5;
        adjacentLoadPages = 2;
      }

      if (isFroYo) {
        adjacentFontLoadPages = 1;
        adjacentLoadPages = 1;
      }



      //////////////////////////////////////////////////////////
      //
      // Font object specific to the FontLoader
      //
      //////////////////////////////////////////////////////////

      function FontLoaderFont (id, shortstyle, family, fallback, weight, style) {
        this.id = id;
        this.shortstyle = shortstyle;
        this.family = family;
        this.fallback = fallback;
        this.weight = weight;
        this.style = style;
      }

      FontLoaderFont.prototype.eotCssRule = function (assetUrl) {
        var fontFaceStr = "src: url(" + assetUrl + this.family + ".eot); " +
            "font-family: " + this.family + "; font-weight: " + this.weight + "; font-style: " + this.style;
        return "@font-face {" + fontFaceStr + "}";
      };

      FontLoaderFont.prototype.ttfCssRule = function (assetUrl) {
        var fontFaceStr = "src: url(" + assetUrl + this.family + ".ttf) format('truetype'); " +
            "font-family: " + this.family + "; font-weight: " + this.weight + "; font-style: " + this.style;
        return "@font-face {" + fontFaceStr + "}";
      };

      FontLoaderFont.prototype.svgCssRule = function (assetUrl) {
        var fontFaceStr = "src: url(" + assetUrl + "#" + this.family + ") format('svg'); " +
            "font-family: " + this.family + "; font-weight: " + this.weight + "; font-style: " + this.style;
        return "@font-face {" + fontFaceStr + "}";
      };

      FontLoaderFont.prototype.createPreloadElem = function () {
        return "<span style='font-family: " + this.family + "'>scribd.</span> ";
        //document.body.appendChild(e);
      };


      //////////////////////////////////////////
      //
      // The FontLoader object
      //
      //////////////////////////////////////////
      function FontLoader (docManager) {
        this.fonts = [];
        this.docManager = docManager;
        this._cssRuleQueue = [];
        this._fontLoadQueue = [];
      }

      // Makes a new style block and adds it to the head
      // This is because manipulating an existing styleblock in
      // some browsers (including FF) causes a redisplay of elements
      FontLoader.prototype._makeNewStyleBlock = function () {
        var style = document.createElement('style');

        if (!window.createPopup) { /* For Safari */
          style.appendChild(document.createTextNode(''));
        }

        var head = document.getElementsByTagName('head')[0];
        head.appendChild(style); // Insert it into the beginning of the head

        return style;
      };

      // We batch update our CSS rules.  We push stuff into the queue, and after
      // the request we append them all to the CSS rule sheet
      //
      // THis is to make it so we don't accidentally trigger calculating new layouts
      // when it is unecessary
      FontLoader.prototype._insertCssRule = function (rule) {
        this._cssRuleQueue.push(rule);
      };

      // Call this at the end of any function that may call _insertCssRule
      FontLoader.prototype._flushCssRuleQueue = function (optionalIdName) {
        if (this._cssRuleQueue.length > 0) {
          var styleElem = (
              optionalIdName &&
              document.getElementById(optionalIdName)) ||
            this._makeNewStyleBlock();

          var cssText = this._cssRuleQueue.join('\n');

          if (isIe()) {
            styleElem.styleSheet.cssText = cssText;
          } else if (!window.createPopup) { /* For Safari */
            styleElem.appendChild(document.createTextNode(cssText));
          } else {
            styleElem.innerHTML = cssText;
          }

          this._cssRuleQueue = [];
        }
      };


      FontLoader.prototype.getFontAggregatorHostForFonts = function (fonts) {
        var fontIds = [];
        for (var i = 0; i < fonts.length; i++) {
          fontIds.push(fonts[i].shortstyle + fonts[i].id);
        }
        fontIds.sort();
        var url = this.docManager.nextFontAggregatorHost() + '/' + this.docManager.assetPrefix + '/' + fontIds.join(',') + '/' + FONT_SERV_VERSION + '/';

        switch(fontLoaderStrategy) {
        case FONT_LOADER_EOT:
          //url += 'eots';
          break;
        case FONT_LOADER_CSS_TTF:
          if (!isFroYo) {
            url += 'ttfs.css';
          }
          break;
        case FONT_LOADER_MULTI_SVG:
          url += 'fonts.svg';
          break;
        }

        return url;
      };
      //FontLoader.prototype._tLoadQueue

      FontLoader.prototype._addTTFRules = function (fonts, assetUrl) {
        for (var i = 0; i < fonts.length; i++) {
          var font = fonts[i];
          this._insertCssRule(font.ttfCssRule(assetUrl));
        }
      };

      FontLoader.prototype._addSVGRules = function (fonts, assetUrl) {
        for (var i = 0; i < fonts.length; i++) {
          var font = fonts[i];
          this._insertCssRule(font.svgCssRule(assetUrl));
        }
      };

      FontLoader.prototype._addEOTRules = function (fonts, assetUrl) {
        for (var i = 0; i < fonts.length; i++) {
          var font = fonts[i];
          this._insertCssRule(font.eotCssRule(assetUrl));
        }
      };


      FontLoader.prototype._nextPreloadId = function () {
        if (!this._preloadId) {
          this._preloadId = 0;
        }

        var id =  "preload_bed" + this._preloadId;

        this._preloadId += 1;

        return id;
      };

      FontLoader.prototype._addCSSWebkit = function (fonts, assetUrl) {

        var self = this;
        var preloadIFrame = document.createElement('iframe');

        function oniFrameLoad () {
          var newPreload = document.createElement('div');
          var preloadId = self._nextPreloadId();
          newPreload.innerHTML = innerHTML;

          var preloadBed = document.getElementById(FONT_PRELOAD_BED_ID);

          //document.body.appendChild(newPreload);

          var intervalId = window.setInterval(
            function () {
              // Wait until the stylesheet loads
              if (preloadIFrame.contentDocument.styleSheets.length > 0) {
                window.clearInterval(intervalId);

                //force style calculation
                preloadIFrame.contentDocument.body.getBoundingClientRect();
                preloadBed.appendChild(newPreload);
                window.setTimeout(function () {
                    //force style calculation
                    preloadIFrame.contentDocument.body.getBoundingClientRect();
                    self._addCSSLink(assetUrl);
                  },
                  500);
              }
            }, 0);
        }

        var preloadId = this._nextPreloadId();

        preloadIFrame.id = preloadId;

        var innerHTML = '';

        for (var i = 0; i < fonts.length; i++) {
          var font = fonts[i];
          innerHTML += font.createPreloadElem();
        }


        var styleElem = this._makeNewStyleBlock();


        preloadIFrame.addEventListener('load', function () {oniFrameLoad();}, false);
        preloadIFrame.style.display = 'none';
        document.body.appendChild(preloadIFrame);
        preloadIFrame.contentDocument.body.innerHTML = innerHTML;


        var link = preloadIFrame.contentDocument.createElement('link');
        link.href = assetUrl;
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.media = 'screen';

        var head = preloadIFrame.contentDocument.getElementsByTagName('head')[0];
        head.appendChild(link); // Insert it into the beginning of the head
      };

      FontLoader.prototype._addCSSLink = function (assetUrl) {
        var link = document.createElement('link');
        link.href = assetUrl;
        link.rel = 'stylesheet';
        link.type = 'text/css';

        var head = document.getElementsByTagName('head')[0];
        head.appendChild(link); // Insert it into the beginning of the head
      };


      FontLoader.prototype.flushFontQueue = function () {
        if (this._fontLoadQueue.length === 0) {
          return;
        }
        if (this.docManager.displayType=='rasterize') {
          return;
        }

        var fontsToLoad = this._fontLoadQueue;
        this._fontLoadQueue = [];


        var assetUrl = this.getFontAggregatorHostForFonts(fontsToLoad);

        switch(fontLoaderStrategy) {
        case FONT_LOADER_EOT:
          this._addEOTRules(fontsToLoad, assetUrl);
          break;
        case FONT_LOADER_CSS_TTF:
          if (isFroYo) {
            this._addTTFRules(fontsToLoad, assetUrl);
          } else if (isWebKit) {
            this._addCSSWebkit(fontsToLoad, assetUrl);
          } else {
            this._addCSSLink(assetUrl);
          }
          break;
        case FONT_LOADER_MULTI_SVG:
          this._addSVGRules(fontsToLoad, assetUrl);
          break;
        }

        this._flushCssRuleQueue();
      };

      FontLoader.prototype.addFontToQueue = function (fontId) {
        var font = this.fonts[fontId];
        if (!font._loadQueued) {
          font._loadQueued = true;
          this._fontLoadQueue.push(font);
        }
      };


      /////////////////////////
      // Public functions
      /////////////////////////
      FontLoader.prototype.addFont = function (id, shortstyle, family, fallback, weight, style) {
        var font = new FontLoaderFont(id, shortstyle, family, fallback, weight, style);
        this.fonts[id] = font;
      };

      /* deprecated */
      FontLoader.prototype.setNumFonts = function (numFonts) {
        for (var i = 0; i < numFonts; i++) {
          this.fonts[i] = new FontLoaderFont(i, "", "ff"+i, "sans-serif", "normal", "normal");
        }
      };

      // Makes styles to overcome the FOUT
      FontLoader.prototype._initHidersCSS = function () {
        var families = [];
        for (var i = 0; i < this.fonts.length; i++) {
          families.push('.' + this.fonts[i].family);
        }
        this._insertCssRule(families.join(', ')  + ' {display: none;}\n');
      };

      // Makes the real styles
      FontLoader.prototype._initFamilyCSS = function () {
        for (var i = 0; i < this.fonts.length; i++) {
          var fam = this.fonts[i].family;
          var fallback = this.fonts[i].fallback;
          var weight = this.fonts[i].weight;
          var style = this.fonts[i].style;

          var selector = 'div.' + fam + ' span';

          // If we have a specific embed div, use that as the root for the css selectors.
          if (typeof(scribd) !== 'undefined' && typeof(scribd.embed_div_id) !== 'undefined') {
            selector = '#' + scribd.embed_div_id + ' ' + selector;
          }

          if(isIe()) {
            // don't do font fallbacks for IE- it will try to slant fonts that are already italic
            this._insertCssRule(selector + ' {font-family: ' + fam + ' !important;\n}');
          } else {
            this._insertCssRule(selector + ' {font-family: ' + fam + ', ' + fallback + '; font-weight: '+weight+'; font-style: '+style+';\n}');
          }
        }
      };

      FontLoader.prototype.initStyles = function (numFonts) {
        if (this.docManager.displayType=='rasterize') {
          return;
        }

        this._initFamilyCSS();
        switch(fontLoaderStrategy) {
        case FONT_LOADER_EOT:
          break;
        case FONT_LOADER_CSS_TTF:
          if (!isFroYo) {
            this._initHidersCSS();
          }
          break;
        case FONT_LOADER_MULTI_SVG:
          break;
        }
        this._flushCssRuleQueue('preload_styler');
      };

      FontLoader.prototype.setupTestElements = function () {

        if (fontLoaderStrategy != FONT_LOADER_CSS_TTF || isWebKit || this.docManager.displayType=='rasterize') {
          return; // we only use this for TTFS and webkit
        }

        var innerHTML = '';

        for (var i = 0; i < this.fonts.length; i++) {
          var font = this.fonts[i];
          innerHTML += font.createPreloadElem();
        }

        var preloadBed = document.getElementById(FONT_PRELOAD_BED_ID);
        preloadBed.innerHTML = innerHTML;
        document.body.appendChild(preloadBed);

        this._insertCssRule('#' + FONT_PRELOAD_BED_ID + ' span {display: block; visibility: hidden}');
        this._flushCssRuleQueue();
      };

      function LoadFontGroup (groupNum, fontLoader) {
        this.pages = [];
        this.loaded = false;
        this.fonts = {}; // Object with fontFamily => true;  Used like a set
        this.numFonts = 0;
        this.fontLoader = fontLoader;
        this.groupNum = groupNum || 0;
      }

      LoadFontGroup.prototype.addPage = function (page) {
        for (var i = 0; i < page.fonts.length; i++) {
          var fontId = page.fonts[i];
          if (this.fonts[fontId] === undefined) {
            this.fonts[fontId] = true;
            this.numFonts += 1;
          }
        }
        this.pages.push(page);
      };


      LoadFontGroup.prototype.isFull = function () {
        var numPages = this.pages.length;
        var groupNum = this.groupNum;
        var numFonts = this.numFonts;

        if (fontLoaderStrategy == FONT_LOADER_EOT) {
          return (
            this.hasLoaded ||
            numFonts > 50 ||
            (numFonts >= 20 && (
                (groupNum === 0 && numPages >= adjacentFontLoadPages + 3) ||
                (numPages >= 15)))
          );
        } else  if (fontLoaderStrategy == FONT_LOADER_MULTI_SVG || isFroYo) {
          return (
            this.hasLoaded ||
            (numFonts >= 5 && numPages >= adjacentFontLoadPages)
          );
        } else {

          return (
            this.hasLoaded ||
            numFonts > 100 ||
            (numFonts >= 20 && (
                (groupNum === 0 && numPages >= adjacentFontLoadPages + 3) ||
                (numPages >= 100)))
          );
        }
      };

      // Defaults to load immediately. deferredDelay is in MS
      LoadFontGroup.prototype.load = function (loadDelay) {
        if (this.hasLoaded) {
          return;
        }

        this.hasLoaded = true;

        var self = this;
        function load () {
          for (var fontId in self.fonts) {
            if (self.fonts.hasOwnProperty(fontId)) {
              self.fontLoader.addFontToQueue(fontId);
            }
          }

          self.fontLoader.flushFontQueue();
        }


        if (loadDelay) {
          window.setTimeout(function () {load();}, loadDelay);
        } else {
          load();
        }
      };

      LoadFontGroup.prototype.newNextGroup = function () {
        return new LoadFontGroup(this.groupNum + 1, this.fontLoader);
      };


      //////////////////////////////////////////////
      // Page Manager FUnctions
      ///////////////////////////////////////////

      var SCALE_METHOD_WEBKIT = 1;
      var SCALE_METHOD_MOZ    = 2;
      var SCALE_METHOD_ZOOM   = 3;
      var SCALE_METHOD_OPERA  = 4;

      // pageScaleMethod is used to determine which CSS attribute we use to scale a page
      var pageScaleMethod = (function() {
          if (document.documentElement.style.WebkitTransform !== undefined) {
            return SCALE_METHOD_WEBKIT;
          } else if (document.documentElement.style.MozTransform !== undefined) {
            return SCALE_METHOD_MOZ;
          } else if (document.documentElement.style.OTransform !== undefined) {
            return SCALE_METHOD_OPERA;
          } else {
            return SCALE_METHOD_ZOOM;
          }
        })();

      // Usually container_elem will be the outer_page_elem
      // Params: see defaultParams for a list of arguments that are needed and descriptiopns
      function Page(params)  {
        // Set the params.  Every param we need should be in _defaultParams
        for (var p in this._defaultParams) {
          if (this._defaultParams.hasOwnProperty(p)) {
            this[p] = params[p] || this._defaultParams[p];
          }
        }

        // Some sanity checks
        for (var i = 0; i < this._requiredParams.length; i++) {
          var param = this._requiredParams[i];
          if (!this[param]) {
            throw "Missing required Page param: " + param;
          }
        }

        if (!this.contentUrl && !this.innerPageElem) {
          throw "Must initialize a page with either a contentUrl or innerPageElem element";
        }

        if (this.containerElem.boundToPageObj === true) {
          throw "Container Elem is already bound to a page.  We shouldn't get here";
        }
        this.containerElem.boundToPageObj = true;

        // This is used to manage whether we have to update the display.  We
        // don't actually have to zoom if we're displaying.  If we're not visible
        // we still need to keep track of whether or not the innerZoom has changed

        // This maintains the width we would like our contents to be.
        // It will generally be set to the last width we set our width to
        //
        // _targetWidth will be null if we don't have any pending zooms
        this._targetWidth = null;

        // We know that the innerPage is visible if it exists at the start
        this._innerPageVisible = !!this.innerPageElem;

        // We haven't turned the images on yet
        this._imagesTurnedOn = false;

        this.boundingRect = null;

        this.isVisible = false;  // Whether or not this page is being displayed.  The CurrentDisplay manager is
                                 // responsible for setting this eagerly
        this.displayDirty = true;  // if we need to update the display even if it is in the same state
        this.displayOn = null;


        this.loadHasStarted = !!this.innerPageElem; //If we've started (or have already finished loading the inner page
      }

      Page.prototype._defaultParams = {
        containerElem: null,  // This is generally the outer_page_x element of the page
        innerPageElem: null,  // Element of the page.  This exists once the page is loaded
        contentUrl: null,     // URL for content (either this or innerPageElem is required)
        origWidth: null,      // Width from manifest of document
        origHeight: null,     // Height from manifest of document
        fonts: null,          // List of font families
        docManager: null,     // The doc manager for the document. DocumentManager automatically injects this
        pageNum: null        // The pageNumber
      };

      Page.prototype._requiredParams = ['origWidth', 'origHeight', 'fonts', 'docManager', 'containerElem', 'pageNum'];



      // ONLY call this after all the outer pages are loaded
      // and after all the elements are zoomed
      //
      // TODO: when in fit to width, don't call this toooo often
      Page.prototype._updateBoundingRect = function () {
        var top, left, width, height;

        if (this.containerElem.getBoundingClientRect && this.docManager.viewportManager.viewRect) {
          var boundingRect = this.containerElem.getBoundingClientRect();

          var vpr = this.docManager.viewportManager.viewRect;

          left = boundingRect.left + vpr.left;
          top = boundingRect.top + vpr.top;

          width = boundingRect.right - boundingRect.left;
          height = boundingRect.bottom - boundingRect.top;

          this.boundingRect = {
            left: left,
            'top': top,
            bottom: top + height,
            right: left + width,
            width: width,
            height: height
          };

       } else {
         top = this.containerElem.offsetTop;
         left = this.containerElem.offsetLeft;
         width = this.containerElem.offsetWidth;
         height = this.containerElem.offsetHeight;

         this.boundingRect = {
           left: left,
           'top': top,
           bottom: top + height,
           right: left + width,
           width: width,
           height: height
         };
       }
        /*
        var top = this.containerElem.offsetTop;
        var left = this.containerElem.offsetLeft;
        var width = this.containerElem.offsetWidth;
        var height = this.containerElem.offsetHeight;

        this.boundingRect = {
          left: left,
          'top': top,
          bottom: top + height,
          right: left + width,
          width: width,
          height: height

        } */
      };

      //////////////////////////////
      // ASYNC Loading Functions
      ////////////////////////////////
      //
      Page.prototype._setContainerContents = function (pageHTML) {
        // XXX This is for the demo only

        var getRidOfNoscripts =  /<noscript *><img[^<>]*\/><\/noscript *>/g;

        // Set the contents of our container to the pageHTML
        this.containerElem.innerHTML = pageHTML.replace(getRidOfNoscripts, '') + this.containerElem.innerHTML;


        var self = this;

        this.innerPageElem = this.containerElem.children[0];
        this.turnOnLinks();
        this.turnOnImages(); // Turn on the images now
        this.fixSVGFonts();


        this.displayDirty = true;
        if (this.displayOn) {
          this.display();
        } else {
          this.hide();
        }
      };


      Page.prototype.fixSVGFonts = function () {
        if (this._svgFontsFixed) {
          throw "Already fixed the svg fonts";
        }

        if (!this.innerPageElem) {
          return;
        }

        if (isMobileSafari) {
          var splitSpaces = function (element) {
            if (element.nodeType == document.TEXT_NODE) {
              var spaceIdx = element.textContent.search(/[  \n][^ \n ]/);

              if (spaceIdx >= 0) {
                splitSpaces(element.splitText(spaceIdx + 1));
              }
            } else {
              var children  = element.childNodes;
              for (var i = 0; i < children.length; i++) {
                splitSpaces(children[i]);
              }
            }
          };

          var addSpans = function (element) {
            var children  = element.childNodes;
            for (var i = 0; i < children.length; i++) {
              var e1 = children[i];
              if (e1.nodeType == document.ELEMENT_NODE) {
                addSpans(e1);
              } else {
                var e2 = children[i+1];
                if (e2 && e2.nodeName == '#text') {
                  element.insertBefore(document.createElement('span'), e2);
                }
              }
            }
          };



          splitSpaces(this.innerPageElem);
          addSpans(this.innerPageElem);
        }
        this._svgFontsFixed = true;
      };


      Page.prototype.imagePageContent = function(imageUrl) {
        str = "<img src='"+ imageUrl +"'></img>";
        return str;
      };

      // Load the page from the json
      Page.prototype.load = function () {
        this.currentlyLoading = true;
        this.loadHasStarted = true;
        // We want to make it so if we call display while its loading, it turns it on after.
        // This gets rid of the race condition where you can't change the visibility of a page state
        // while it is loading

        if (this.innerPageElem) {
          throw "We already have loaded this page, but it looks like you called loadPage again";
        }

        this.loadFonts(); // When loading a page, start the loading of its fonts

        var callbackName = 'page' + this.pageNum + '_callback';

        //Sanity Check
        if (window[callbackName]) {
          // page callback is being redefined, garbage collect the old function first.
          try {
            delete window[callbackName]; // Surround with TRY because we can't do this with IE
          } catch (err) {
            // Just clean up the callback we set
            window[callbackName] = undefined;
          }
        }

        if (this.docManager.displayType == 'rasterize') {
            delete this.currentlyLoading;
            this._setContainerContents(this.imagePageContent(this.contentUrl));
            return;
        }

        // Set up a jsonp callback
        var s = document.createElement('script');

        // This will be called once the static jsonp file is loaded
        // "contents" will be an array with 1 string element.  This is the
        // body of the page
        var self = this;
        window[callbackName] = function (contents) {
          // Remove the script that we added
          document.body.removeChild(s);
          var pageHTML = contents[0];

          // We're not loading anymore
          delete self.currentlyLoading;

          // Set the contents of our container to
          // the page contents
          //
          // setContainerContents will either display or hide the page
          // based on the this.displayOn variable
          self._setContainerContents(pageHTML);


          self.docManager.fireEvent('pageLoaded', self.containerElem);

          try {
            delete window[callbackName]; // Surround with TRY because we can't do this with IE
          } catch (err) {
            // Just clean up the callback we set
            window[callbackName] = undefined;
          }
        };
       s.src = this.contentUrl;
       s.type = 'text/javascript';
       s.charset = 'UTF-8';
       document.body.appendChild(s);
      };

      // Removes the page from the DOM and resets its load state
      Page.prototype.remove = function() {
        if (this.innerPageElem) {
          var p = this.innerPageElem.parentNode;
          p.removeChild(this.innerPageElem);
          delete this.innerPageElem;
          delete this.currentLoading;
          delete this.loadHasStarted;
          this._linksTurnedOn = false;
          this._imagesTurnedOn = false;
          this._svgFontsFixed = false;
        }
      };

      ///////////////////////////////////////////
      // Visibility functions
      // (hiding and showing the page)
      //
      //////////////////////////////////////////

      // forceLoad is option.  if true, it will load the page if it hasn't been loaded yet
      Page.prototype.display = function (forceLoad, dontTurnOn) {
        if (this.displayOn && !this.displayDirty) {
          return;
        }

        this.displayOn = true;

        if (this.currentlyLoading) {
          return;
        } else if (!this.innerPageElem) {
          if (this.loadHasStarted) {
            return;
          } else if (forceLoad) {
            this.load();
            return;
          } else {
            return;
          }
        }

        this.displayDirty = false;


        if (!dontTurnOn) {
          // If we haven't turned on our images yet, we need to
          if(!this._linksTurnedOn) {
            this.turnOnLinks();
          }

          // If we haven't turned on our images yet, we need to
          if(!this._imagesTurnedOn) {
            this.turnOnImages();
          }


          // If we haven't turned on our images yet, we need to
          if(!this._svgFontsFixed) {
            this.fixSVGFonts();
          }

        }

        this.loadFonts(); // When loading a page, start the loading of its fonts

        // if we're laready visible, return
        if (this._innerPageVisible) {
          return;
        }

        this.containerElem.className = this.containerElem.className.replace(/placeholder|not_visible/g, '');
        this._innerPageVisible = true;
        if (!dontTurnOn) {
          this._fitContentsToWidth(); // This will update the zoom if it has changed while we've been away
          this.innerPageElem.style.display = 'block';
        }
      };

      Page.prototype.hide = function () {
        if (!this.displayOn && !this.displayDirty) {
          return;
        }

        this.displayOn = false;

        if (!this.innerPageElem) {
          return;
        }

        this.displayDirty = false;

        this.containerElem.className = this.containerElem.className + ' not_visible';
        this._innerPageVisible = false;
        this.innerPageElem.style.display = 'none';
      };

      Page.prototype.setLoadFontGroup = function (loadFontGroup) {
        loadFontGroup.addPage(this);
        this.loadFontGroup = loadFontGroup;
      };

      Page.prototype.loadFonts = function () {
        this.loadFontGroup.load();
      };

      var isIe6 = !!( document.all && (/msie 6./i).test(navigator.appVersion) && window.ActiveXObject );

      /////////////////////////////////////////////
      // RESIZING functions (zooming and whatnot)
      /////////////////////////////////////////////
      Page.prototype._setZoomScale = function(val) {
        var e = this.innerPageElem;
        switch (pageScaleMethod) {
        case SCALE_METHOD_WEBKIT:
          e.style.WebkitTransform = 'scale(' + val + ')';
          e.style.WebkitTransformOrigin = 'top left';
          break;

        case SCALE_METHOD_MOZ:
          e.style.MozTransform = 'scale(' + val + ')';
          e.style.MozTransformOrigin = 'top left';
          break;

        case SCALE_METHOD_OPERA:
          e.style.OTransform = 'scale(' + val + ')';
          e.style.OTransformOrigin = 'top left';
          break;

        case SCALE_METHOD_ZOOM:
          if (!e.originalZoom) {
            // Current style for zoom is in percent
            // NOTE: This only works in IE.
            e.originalZoom = e.currentStyle.zoom == 'normal' ? 1.0 : parseFloat(e.currentStyle.zoom) / 100.0;
            if (isIe6 && !this.docManager._isEmbed) {
              e.originalZoom *= 1.35;
            }
          }
          e.style.zoom = (e.originalZoom * val * 100.0) + '%';
          if(isIe6) {
            // force IE to rerender the element... dammit.  this is some pretty hacky stuff.
            var p = this.innerPageElem;
            setTimeout(function() {
              p.style.marginLeft = p.style.marginLeft === '' ? 0 : '';
            }, 500);
          }
          break;

        default:
          throw "Unknown scale method " + pageScaleMethod;
        }
      };


      // This changes the zoom of the innerPageElem. If the page isn't loaded yet
      // we don't do anything
      //
      // it will set the width to _targetWidth and then set it to null
      Page.prototype._fitContentsToWidth = function() {
        if (this._targetWidth && this.innerPageElem && this._innerPageVisible) {
          var multiplier = this._targetWidth / this.origWidth;
          this._setZoomScale(multiplier);
          this._targetWidth = null;
        }
      };

      Page.prototype.setWidth = function (width) {
        var height = Math.ceil((width/this.origWidth) * this.origHeight);
        this.containerElem.style.width = width + "px";
        this.containerElem.style.height = height + "px";
        this._targetWidth = width;
        this._fitContentsToWidth();
      };

      Page.prototype.setBounds = function(width, height) {
        if(this.origWidth / this.origHeight > width / height) {
          height = Math.ceil((width/this.origWidth) * this.origHeight);
        } else {
          width = Math.ceil((height/this.origHeight) * this.origWidth);
        }

        this.containerElem.style.width = width + "px";
        this.containerElem.style.height = height + "px";

        this._targetWidth = width;
        this._fitContentsToWidth();
      };


      /////////////////////////////////////////
      // Lazy Image Loading Functions
      /////////////////////////////////////////


      // The page's images are set to use the 'orig' attribute instead of 'src'
      // This is so we can control
      Page.prototype.turnOnImages = function () {
        if (!this.innerPageElem) {
          throw "Can't turn on images for a page that's not loaded";
        }

        // Sanity check
        if (this._imagesTurnedOn) {
          throw "Images have already been turned on for this document";
        }

        this._imagesTurnedOn = true;

        var elemsToCheck = this.innerPageElem.getElementsByTagName('img');
        for (var i = 0; i < elemsToCheck.length; i++) {
          var img = elemsToCheck[i];
          if (img.className.toLowerCase().search('absimg') > -1) {  // Is this an absimg?
            if (!img.src) {
              var inputUrl = this.docManager.subImageSrc(img.getAttribute('orig'));
              if (this.docManager.enablePNGHack) {
                img.style.filter = "progid:DXImageTransform.Microsoft.AlphaImageLoader(src='" + inputUrl + "', sizingMethod='scale')";
                img.src = ie6_pngfix_shim;
              } else {
                // move the orig attribute to the src.  Also, set the display to block
                img.src = inputUrl;
              }
              img.removeAttribute('orig');
              img.style.display = 'block';
            }
          }
        }
      };

      // The page's images are set to use the 'orig' attribute instead of 'src'
      // This is so we can control
      Page.prototype.turnOnLinks = function () {
        if (!this.innerPageElem) {
          throw "Can't turn on links for a page that's not loaded";
        }

        // Sanity check
        if (this._linksTurnedOn) {
          throw "Links have already been turned on for this document";
        }



        this._linksTurnedOn = true;

        function make_handler(href) {
            return (function() {
              window.location.hash = '#outer_page_' + href.substring(4);
            });
        }

        var elemsToCheck = this.innerPageElem.getElementsByTagName('a');
        for (var i = 0; i < elemsToCheck.length; i++) {
          var a = elemsToCheck[i];
          if (a.className.toLowerCase().search('ll') > -1) {  // Is this an absimg?
            if (!a.href) {
              var orig = a.getAttribute('orig');
              if (orig) {
                var href = Base64.decode(orig).replace(/^j[\W]*a[\W]*v[\W]*a[\W]*s[\W]*c[\W]*r[\W]*i[\W]*p[\W]*t[\W]*:|^f[\W]*i[\W]*l[\W]*e[\W]*:/ig, "");
                if (href.search(/^page/) > -1) {
                  // internal link
                  a.onclick = make_handler(href);
                } else {
                  // external link
                  if(href.search(/^mailto:/) >= 0) {
                      // leave mailto links alone
                  } else if(href.search(/^(http|ftp)/) < 0) {
                      href = "http://"+href;
                  }
                  a.target = "_blank";
                  set_href(a, href);
                  a.rel = "nofollow";
                }
              }
            }
          }
        }
      };

      function ViewportManager() {
        this.initEventHelper();

        this.viewRect = null;

        // Our callbacks are objects so we can remove them
        // Think of them more as "set" datatypes.  The value doesn't matter

        this.enabled = false;

        var self = this;

        // Wrap eventHandler
        this._scrollCallback = function () {
          self._eventHandler('scroll');
        };
        // Wrap eventHandler
        this._resizeCallback = function (e) {
          self._eventHandler('resize');
        };
      }

      addEventHelper(ViewportManager, ['vertical', 'horizontal', 'either', 'resize']);

      // broken for the iPad!
      ViewportManager.prototype._makeViewRect = function () {
        var de = document.documentElement;
        var top = window.scrollY || window.pageYOffset || de.scrollTop;
        var left = window.scrollX || window.pageXOffset || de.scrollLeft;
        var width = window.innerWidth || de.clientWidth;
        var height = window.innerHeight || de.clientHeight;

        var right = left + width;
        var bottom = top + height;

        return {
          'top': top,
          left: left,
          right: right,
          bottom: bottom,

          width: width,
          height: height
        };
      };

      ViewportManager.prototype._updateViewRect = function() {
        var oldViewRect = this.viewRect;
        this.viewRect = this._makeViewRect();
        var xChanged = !oldViewRect || oldViewRect.left != this.viewRect.left || oldViewRect.width != this.viewRect.width; // don't need to compare right
        var yChanged = !oldViewRect || oldViewRect.top != this.viewRect.top || oldViewRect.height != this.viewRect.height; // don't need to compare bottom

        return {
          xChanged: xChanged,
          yChanged: yChanged
        };
      };

      ViewportManager.prototype._eventHandler = function (eventType) {
        var changes = this._updateViewRect();

        if((eventType == 'resize' || eventType == 'both') && (changes.xChanged || changes.yChanged)) {
          this.fireEvent('resize', this.viewRect);
        }

        // Call the callbacks that fire when either horizontal or vertical change
        if (changes.xChanged || changes.yChanged) {
          this.fireEvent('either', this.viewRect);
        }

        // Call the callbacks that fire when the horizontal stuff change
        if (changes.xChanged) {
          this.fireEvent('horizontal', this.viewRect);
        }


        // Call the callbacks that fire when the vertical stuff change
        if (changes.yChanged) {
          this.fireEvent('vertical', this.viewRect);
        }
      };


      ViewportManager.prototype.enable = function () {
        if (this.enabled) {
          throw "ViewportManager has already been enabled";
        }
        this.enabled = true;
        this.container = window;
        this._eventHandler('both'); // Call it once to prime the pump and see if things changed since we last have been here
        if (window.addEventListener) {
          window.addEventListener('resize', this._resizeCallback, false);
          // We prefer scroll on the document because iPhone supports it
          window.document.addEventListener('scroll', this._scrollCallback, false);
        } else if (window.attachEvent) { // This is for IE.
          window.attachEvent('onresize', this._resizeCallback);
          window.attachEvent('onscroll', this._scrollCallback); // IE doesn't support scroll events for the document
        }
      };

      ViewportManager.prototype.disable = function () {
        if (!this.enabled) {
          throw "ViewportManager has already been disabled";
        }
        this.enabled = false;

        if (this.container.removeEventListener) {
          window.removeEventListener('resize', this._resizeCallback, false);
          this.container.removeEventListener('scroll', this._scrollCallback, false);
        } else if (window.detatchEvent) {
          window.detatchEvent('onresize', this._resizeCallback);
          this.container.detatchEvent('onscroll', this._scrollCallback);
        }
      };

      //
      // ViewManager (abstract)
      //
      // override the _methods
      //

      function ViewManager() { }

      ViewManager.prototype.name = function() {
        return this._name;
      };

      ViewManager.prototype.register = function(documentManager, viewportManager) {
        if (this.registered) {
          throw "This ViewManager is already registered";
        }
        this.registered = true;

        this.documentManager = documentManager;
        this.viewportManager = viewportManager;

        this._currentPageWidth = defaultViewWidth;
        this._currentZoomMultiplier = 1.0;
        this._updatePageWidths();

        var targetPage = this.documentManager.firstVisiblePage;

        this._register(documentManager, viewportManager);

        if (targetPage) {
          this.documentManager.gotoPage(targetPage.pageNum, { pretty: false });
        }
      };

      ViewManager.prototype._zoomedPageWidth = function() {
        return this._currentPageWidth * this._currentZoomMultiplier;
      };

      ViewManager.prototype._updatePageWidths = function() {
        this.documentManager.setPageWidths(this._zoomedPageWidth());
      };

      // Probably only need to override this for the Scroll view manager
      //
      // This tells the document manager if it should scroll to the top of the
      // current page or go the previous page(when scrolling up)
      ViewManager.prototype.isTopPageInView = function() {
        return true;
      };

      ViewManager.prototype._register = function(documentManager, viewportManager) {
        // optional method
      };

      ViewManager.prototype.unregister = function() {
        if (!this.registered) {
          throw "This ViewManager is already unregistered";
        }

        if (this.isFullscreen) {
          this.exitFullscreen();
        }

        this._checkBodyWidth();

        this._unregister();

        this.registered = false;
        delete this.documentManager;
        delete this.viewportManager;
      };

      ViewManager.prototype._unregister = function() {
        // optional method
      };

      ViewManager.prototype._pagingStep = function() {
        return 1;
      };

      ViewManager.prototype.gotoPage = function(pageNum, options) {
        if (!this.registered) {
          throw 'ViewManager must be registerd to call gotoPage';
        }

        this._gotoPage(pageNum, options);
      };

      ViewManager.prototype._gotoPage = function(pageNum, options) {
        // override me
      };

      ViewManager.prototype._fireHideExtras = function() {
        this.documentManager._fireHideExtras();
        this._extrasHidden = true;
      };

      ViewManager.prototype._fireShowExtras = function() {
        this.documentManager._fireShowExtras();
        this._extrasHidden = false;
      };

      ViewManager.prototype.enterFullscreen = function() {
        if(this.isFullscreen) {
          throw 'Fullscreen is already set';
        }

        this._checkBodyWidth();
        this.viewportManager.addEvent('resize', this._fullscreenResizedCallback);
        this._fireHideExtras();
        this.resetZoom();

        this._enterFullscreen();

        this._fullscreenResized(this.viewportManager.viewRect);
        this._currentPageWidth = this.viewportManager.viewRect.width;
        this.isFullscreen = true;

        var targetPage = this.documentManager.firstVisiblePage;
        if(targetPage) {
          this.documentManager.gotoPage(targetPage.pageNum, { pretty: false });
        }

        this.documentManager._fireEnteredFullscreen();
      };

      ViewManager.prototype.exitFullscreen = function() {
        if(!this.isFullscreen) {
          throw 'Fullscreen is not set';
        }

        this.viewportManager.removeEvent('resize', this._fullscreenResizedCallback);
        this._fireShowExtras();
        this.resetZoom();

        this._exitFullscreen();

        this.isFullscreen = false;

        var targetPage = this.documentManager.firstVisiblePage;

        if(targetPage) {
          this.documentManager.gotoPage(targetPage.pageNum, { pretty: false });
        }

        this.documentManager._fireExitedFullscreen();
      };

      ViewManager.prototype._viewBarWidth = function() {
        if(this._extrasHidden) {
          return 0.0;
        } else {
          return this.documentManager.options.extrasWidth;
        }
      };


      ViewManager.prototype._enterFullscreen = function() {
        // override me
      };

      ViewManager.prototype._exitFullscreen = function() {
        // override me
      };

      // Called every time the browser is resized when in fullscreen mode
      ViewManager.prototype._fullscreenResized = function(viewRect) {
        // override me
      };

      ViewManager.prototype._scrollWithZoom = function(viewRect, multiplier) {
        window.scrollTo(0, viewRect.top * multiplier);
      };

      ViewManager.prototype.zoom = function(multiplier) {
        var oldViewRect = this.viewportManager.viewRect;
        if (!oldViewRect) {
          return;
        }
        this._currentZoomMultiplier *= multiplier;
        this._checkBodyWidth();
        this._updatePageWidths();
        this.documentManager.setIsScrolling(true);
        this._scrollWithZoom(oldViewRect, multiplier);
        this._zoomed();
        this.documentManager.setIsScrolling(false);
        this.documentManager._fireZoomed(multiplier);
      };

      ViewManager.prototype._zoomed = function() {
        // override me
      };

      ViewManager.prototype.resetZoom = function() {
        this._currentZoomMultiplier = 1.0;
        this._checkBodyWidth();
        this._updatePageWidths();
        this._zoomed();
      };

      // This sets the width of the body to a fixed number if it's wider than
      // the current window width
      ViewManager.prototype._checkBodyWidth = function (pageWidth) {
        var windowWidth = document.documentElement.clientWidth;
        var targetWidth = this._zoomedPageWidth() + this._viewBarWidth() + 10;

        globalHeader = document.getElementById('global_header'); // XXX XXX Make this non-hardcoded

        if (targetWidth > windowWidth) {
          document.body.style.width = targetWidth + 'px';
          if (globalHeader) {
            globalHeader.style.width = windowWidth + 'px';
          }
        } else {
          document.body.style.width = '100%';
          if (globalHeader) {
            globalHeader.style.width = '100%';
          }
        }
      };


      //////////////
      // Animation
      //////////////

      // Scroll so that the given target is at the top of the screen.
      // Duration is in milliseconds.
      function animateScroll (target, duration, callback) {
        if (typeof $ === 'undefined' && typeof scribd !== "undefined" ) {
          DocumentManager.setJQuery(scribd.jQuery);
        }
        $('html, body').animate({
          scrollTop: $(target).offset().top
        }, {
          queue: false,
          duration: duration,
          easing: 'linear',
          complete: callback
        });
      }


      //
      //  BookViewManager
      //
      function BookViewManager() {
        this._name = 'book';
        this.currentPageId = null;
        var self = this;

        this._fullscreenResizedCallback = function(rect) {
          self._fullscreenResized(rect);
        };
      }

      BookViewManager.prototype = new ViewManager();

      BookViewManager.prototype._register = function(documentManager, viewportManager) {
        this._prepareDisplay();
      };

      BookViewManager.prototype._unregister = function() {
        for(var pageId in this.documentManager.pages) {
          if (this.documentManager.pages.hasOwnProperty(pageId)) {
            var page = this.documentManager.pages[pageId];
            $(page.containerElem).removeClass("book_view");
            page.containerElem.style.display = '';
          }
        }
      };

      BookViewManager.prototype._prepareDisplay = function() {
        for(var pageId in this.documentManager.pages) {
          if (this.documentManager.pages.hasOwnProperty(pageId)) {
            var page = this.documentManager.pages[pageId];
            $(page.containerElem).addClass("book_view");
            page.containerElem.style.display = 'none';
            page.hide();
          }
        }

        this.documentManager.setPageMissingModulesVisible(false);

        // force page jump for initial defaultViewMode == 'book'
        this.documentManager.gotoPage(this.documentManager.currentPageNum() || 1);
      };

      BookViewManager.prototype._zoomed = function() {
        var page = this.documentManager.pages[this.currentPageId];
      };

      BookViewManager.prototype._updatePageWidths = function() {
        // Display two pages side by side, each half as wide as the display area.
        // The _zoomedPageWidth for book view actually refers to the width of
        // both pages together.
        this.documentManager.setPageWidths(this._zoomedPageWidth() / 2);
      };

      BookViewManager.prototype._pagingStep = function() {
        // Since we have two pages on screen, hitting the next or previous button
        // changes the page number by two.
        return 2;
      };

      BookViewManager.prototype._showPage = function(pageId) {
          var page = this.documentManager.pages[pageId];
          if(page) {
            page.isVisible = true;
            page.display(true);
            page.containerElem.style.display = '';
          }
      };

      BookViewManager.prototype._hidePage = function(pageId) {
          var page = this.documentManager.pages[pageId];
          if(page) {
            page.isVisible = false;
            page.containerElem.style.display = 'none';
            page.hide();
          }
      };

      BookViewManager.prototype._gotoPage = function(pageId, options) {
        // When we go to a page, we define this as going to the page on the left.
        // Notice that it is valid to go to page 0, as well as to the last page.
        // In these cases, the other page will be blank.

        // We default to having odd pages on the right, as per publishing convention:
        // http://en.wikipedia.org/wiki/Recto_and_verso
        // TODO: have an option to put odd pages on the left.
        if (pageId % 2 == 1) {
          pageId -= 1;
        }

        var left_page = null; // Verso
        var right_page = null; // Recto

        // Hide the old pages before we switch.
        if (typeof (this.currentPageId) == 'number') {
          this._hidePage(this.currentPageId);
          this._hidePage(this.currentPageId + 1);
        }

        // Get the left and right pages.
        left_page = this.documentManager.pages[pageId];
        right_page = this.documentManager.pages[pageId + 1];

        // If both of the pages are not available, exit early.
        if (!left_page && !right_page) { return; }

        this.currentPageId = pageId;

        if(this.isFullscreen) {
          this._setPageBounds(this.viewportManager.viewRect);
        }

        // Show the new pages.
        this._showPage(pageId);
        this._showPage(pageId + 1);

        // Inform the doc manager that page visibility changed.
        this.documentManager.visiblePagesChanged();
      };


      BookViewManager.prototype._setWidth = function(width) {
        this._currentPageWidth = width;
        this.documentManager.setPageWidths(width);
      };

      BookViewManager.prototype._fullscreenResized = function(viewRect) {
        this._setWidth(viewRect.width - pagePadding);
      };

      BookViewManager.prototype._enterFullscreen = function() {
        this._previousPageWidth = this._currentPageWidth || defaultViewWidth;
        animateScroll(this.documentManager.pages[this.currentPageId].containerElem, 300);
      };

      BookViewManager.prototype._exitFullscreen = function() {
        this._setWidth(defaultViewWidth);
        this._checkBodyWidth();
      };




      //
      //  SlideViewManager
      //
      function SlideViewManager() {
        this._name = 'slideshow';
        this.currentPageId = null;
        var self = this;

        this._fullscreenResizedCallback = function(rect) {
          self._fullscreenResized(rect);
        };
      }

      SlideViewManager.prototype = new ViewManager();

      SlideViewManager.prototype._register = function(documentManager, viewportManager) {
        this._prepareDisplay();
        var scroll_preventer = document.getElementById('scroll_preventer');
        if (scroll_preventer) {
          scroll_preventer.style.overflow = 'hidden';
          scroll_preventer.style.height = '100%';
        }
      };

      SlideViewManager.prototype._unregister = function() {
        var scroll_preventer = document.getElementById('scroll_preventer');
        if (scroll_preventer) {
          scroll_preventer.style.overflow = 'visible';
          scroll_preventer.style.height = 'auto';
        }
      };

      SlideViewManager.prototype._prepareDisplay = function() {
        for(var pageId in this.documentManager.pages) {
          if (this.documentManager.pages.hasOwnProperty(pageId)) {
            var page = this.documentManager.pages[pageId];
            page.containerElem.style.display = 'none';
            page.hide();
          }
        }

        this.documentManager.setPageMissingModulesVisible(false);

        // force page jump for initial defaultViewMode == 'slideshow'
        this.documentManager.gotoPage(this.documentManager.currentPageNum() || 1);
      };

      SlideViewManager.prototype._setPageBounds = function(bounds) {
        var page = this.documentManager.pages[this.currentPageId];
        if(page) {
          page.setBounds(bounds.width, bounds.height);
        }
      };

      SlideViewManager.prototype._gotoPage = function(pageId, options) {
        if (!this.documentManager.pages.hasOwnProperty(pageId)) {
          return;
        }

        var page;

        if (this.currentPageId) {
          page = this.documentManager.pages[this.currentPageId];
          if(page) {
            page.isVisible = false;
            page.containerElem.style.display = 'none';
            page.hide();
          }
        }

        this.currentPageId = pageId;
        page = this.documentManager.pages[pageId];

        if(this.isFullscreen) {
          this._setPageBounds(this.viewportManager.viewRect);
        }

        page.isVisible = true;
        page.display(true);
        page.containerElem.style.display = '';
        page._updateBoundingRect();

        // inform the doc manager that page visibility changed
        this.documentManager.visiblePagesChanged();
      };

      SlideViewManager.prototype._setWidth = function(width) {
        this._currentPageWidth = width;
        this.documentManager.setPageWidths(width);
      };

      SlideViewManager.prototype._fullscreenResized = function(viewRect) {
        this._setPageBounds(viewRect);
      };

      SlideViewManager.prototype._enterFullscreen = function() {
        this._previousPageWidth = this._currentPageWidth || defaultViewWidth;
        animateScroll(this.documentManager.pages[this.currentPageId].containerElem, 300);
      };

      SlideViewManager.prototype._exitFullscreen = function() {
        this._setWidth(defaultViewWidth);
        this._checkBodyWidth();
      };


      //////////////////////
      // ScrollViewManager
      //////////////////////

      function ScrollViewManager() {
        this._name = 'scroll';

        var self = this;

        this._verticalPositionChangeCallback = function () {
          self.checkAndUpdateVisiblePages();
        };
        this._fullscreenResizedCallback = function () {
          self._fullscreenResized();
        };

        this._afterGotoPage = function() {
          self.documentManager.setIsScrolling(false);
          if (!self.isScrolling) {
            self.documentManager.visiblePagesChanged();
            if (self._scrollEffect) {
              delete self._scrollEffect;
            }
          }
        };
      }

      ScrollViewManager.prototype = new ViewManager();


      // Updates whether or not the page is visible.
      // Returns true if the value has changed
      ScrollViewManager.prototype._updateInViewport = function (page) {
        var vpr = this.viewportManager.viewRect; // Make it shorter :P
        var br = page.boundingRect;  // Our bounding rect

        //See if our bounding rect intersects with the viewport rectangle
        var oldVisible = page.isVisible;
        if (!vpr || !br) {
          page.isVisible = false;
        } else {
          page.isVisible = (
            br.left < vpr.right &&
            br.right > vpr.left &&
            br.top < vpr.bottom &&
            br.bottom > vpr.top);
        }

        this.adjacentVisiblePages = 2; // How many adjacent visible pages do we need?

        return oldVisible != page.isVisible;
      };

      ScrollViewManager.prototype.checkAndUpdateVisiblePages = function () {
        var hasChanged = false;
        for (var p in this.pages) {
          if (this.pages.hasOwnProperty(p)) {
            var page = this.pages[p];
            var curPageHasChanged = this._updateInViewport(page);

            // TODO right now we only have the current pages in viewport be visible
            hasChanged = hasChanged || curPageHasChanged;
          }
        }

        if (hasChanged) {
          // If we get here, we know that  the vsibility of a page has changed
          this.documentManager.visiblePagesChanged();
        } else {
          this.documentManager.scheduleLogPageView();
        }
        this._updateDisplayOnPages();
      };


      // Turn display on and off for pages
      // Set a timer to do this only max of once every N ms so we can have smoother scrollings
      ScrollViewManager.prototype._updateDisplayOnPages = function () {
        if (this.documentManager.firstVisiblePage && this.documentManager.lastVisiblePage) {
          var firstVisiblePageNum = this.documentManager.firstVisiblePage.pageNum - this.adjacentVisiblePages;
          var lastVisiblePageNum = this.documentManager.lastVisiblePage.pageNum + this.adjacentVisiblePages;

          // Some of these will be invalid page numbers, but we check
          for(var p in this.pages) {
            if (this.pages.hasOwnProperty(p)) {

              var page = this.pages[p];
              if (page) {
                if (page.pageNum >= firstVisiblePageNum &&  page.pageNum <= lastVisiblePageNum) {
                  page.display();
                } else {
                  page.hide();
                  this.documentManager.fireEvent('pageHide', page);
                }
              }
            }
          }
        }
      };

      ScrollViewManager.prototype._zoomed = function() {
        this.checkAndUpdateVisiblePages();
      };

      ScrollViewManager.prototype._register = function (documentManager, viewportManager) {
        this.pages = documentManager.pages;
        this.viewportManager.addEvent('vertical', this._verticalPositionChangeCallback);

        for(var pageId in this.pages) {
          if (this.pages.hasOwnProperty(pageId)) {
            var page = this.documentManager.pages[pageId];
            page.containerElem.style.display = '';
          }
        }

        this.documentManager.setPageMissingModulesVisible(true);

        // Initialize our junk
        this.documentManager._updatePageBoundingRects();
        this.checkAndUpdateVisiblePages();
      };

      ScrollViewManager.prototype.isTopPageInView = function () {
        var firstPage = this.documentManager.firstVisiblePage;

        if (firstPage) {

          // This happens sometimes when the view height is taller than one page and we are scrolled to the last page.
          if (this.documentManager._expectedFirstPageNum > firstPage.pageNum){
            return true;
          }

          return firstPage.boundingRect.top + 5.0 >= this.viewportManager.viewRect.top;
        } else {
          // If we don't have a first page object, let's let the document scroll
          // to the next page anyways
          return true;
        }
      };


      ScrollViewManager.prototype._unregister = function () {
        this.viewportManager.removeEvent('vertical', this._verticalPositionChangeCallback);
        delete this.pages;
      };

      // Pagination

      ScrollViewManager.prototype._gotoPage = function(pageId, options) {
        // this will be dead code as soon as cache purge is done.
        if (typeof $ === 'undefined' && typeof scribd !== "undefined") {
          DocumentManager.setJQuery(scribd.jQuery);
        }
        if (!this.pages.hasOwnProperty(pageId)) {
          return;
        }

        var page = this.documentManager.pages[pageId];
        this.documentManager.setIsScrolling(true);

        var eligible_for_pretty_scrolling = typeof($.scrollTo) !== 'undefined';

        if (options.pretty && eligible_for_pretty_scrolling) {
          var boundingRectToScrollTo = page.boundingRect;
          if(options.frac) {
            var newTop = page.boundingRect.top + Math.floor(page.boundingRect.height * options.frac);
            boundingRectToScrollTo = $.extend({}, page.boundingRect, {top: newTop});
          }
          $.scrollTo(boundingRectToScrollTo, {duration: 600, onAfter: this._afterGotoPage});
        }
        else { // options.pretty == false
          page._updateBoundingRect();
          scrollTo(page.boundingRect.left, page.boundingRect.top);
          this._afterGotoPage();
        }

        return page.pageNum;
      };

      ScrollViewManager.prototype._gotoNextPage = function() {
        if (!this.documentManager.firstVisiblePage) {
          return;
        }
        this.documentManager.gotoPage(this.documentManager.firstVisiblePage.pageNum + 1, {'direction' : 1});
      };

      ScrollViewManager.prototype._gotoPreviousPage = function() {
        if (!this.documentManager.firstVisiblePage) {
          return;
        }

        this.documentManager.gotoPage(this.documentManager.firstVisiblePage.pageNum - 1, {'direction' : -1});
      };


      // Fullscreen

      ScrollViewManager.prototype._setWidth = function(width) {
        this._currentPageWidth = width;
        this._updatePageWidths();
        this._checkBodyWidth();
      };

      ScrollViewManager.prototype._fullscreenResized = function() {
        this._setWidth((window.innerWidth || document.documentElement.clientWidth) - pagePadding);
      };

      ScrollViewManager.prototype._enterFullscreen = function() {
        this._previousPageWidth = this._currentWidth || defaultViewWidth;
      };

      ScrollViewManager.prototype._exitFullscreen = function() {
        this._setWidth(this._previousPageWidth);
      };

      function DocumentManager(defaultViewMode, mobile, options) {
        this.options = options || {};
        this.options.extrasWidth = this.options.extrasWidth || extrasWidth;

        this.defaultViewMode = (defaultViewMode || 'scroll');
        this.mobile = (mobile || false);

        this.initEventHelper();
        this.pages = {};
        this._pageWidths = null;
        this._fontLoader = new FontLoader(this);

        this.viewManagers = {
          'scroll': new ScrollViewManager(),
          'slideshow': new SlideViewManager(),
          'book': new BookViewManager()
        };


        // The viewport Manager (abbreviated for short)
        this.viewportManager = new ViewportManager();

        this._currentFontAggregatorHostIdx = 0;

        this.visiblePages = [];
        this.firstVisiblePage = null;
        this.lastVisiblePage = null;

        this.currentFontGroup = new LoadFontGroup(0, this._fontLoader);

        this.isScrolling = false;
        this._scrollingCount = 0;
      }

      addEventHelper(DocumentManager, [
        'expectedFirstPageChanged', // Passes in the new first page
        'viewmodeChanged',
        'enteredFullscreen',
        'exitedFullscreen',
        'hideExtras',
        'showExtras',
        'zoomed', // Passes in the zoom multiplier
        'pageHide',
        'pageLoaded',
        'allPagesAdded',
        'pageView',
        'viewmodeInitialized'
        ]);

      DocumentManager.prototype._fireZoomed = function(multiplier) {
        this.fireEvent('zoomed', multiplier);
      };

      DocumentManager.prototype.nextFontAggregatorHost = function () {
        this._currentFontAggregatorHostIdx = (this._currentFontAggregatorHostIdx + 1) % this.fontAggregatorHosts.length;
        return this.fontAggregatorHosts[this._currentFontAggregatorHostIdx];
      };

      DocumentManager.prototype._fireHideExtras = function() {
        this.fireEvent('hideExtras');
      };

      DocumentManager.prototype._fireShowExtras = function() {
        this.fireEvent('showExtras');
      };

      DocumentManager.prototype.currentPageNum = function() {
        return this._expectedFirstPageNum;
      };

      DocumentManager.prototype.setupTestElements = function () {
        this._fontLoader.setupTestElements();
      };

      DocumentManager.prototype.pageCount = function() {
        if(this.hasOwnProperty('_pageCount')) {
          return this._pageCount;
        }
        var i = 0;
        for(var p in this.pages) {
          if (this.pages.hasOwnProperty(p)) {
          i++;
          }
        }
        this._pageCount = i;
        return this._pageCount;
      };

      DocumentManager.prototype.setupPaidDocument = function(allowedPages, originalPageCount) {
          this.allowedPages = allowedPages;
          this.originalPageCount = originalPageCount;
          this._allowedPagesHash = [];
          this._maximumAllowedPage = Math.max.apply(null, this.allowedPages);
          this._minimumAllowedPage = Math.min.apply(null, this.allowedPages);
          this._isPaidDocument = true;
          this._pageMissingElements = [];
          for (var i=0; i < allowedPages.length; i++) {
              this._allowedPagesHash[allowedPages[i]] = true;
              if ((i > 0 && allowedPages[i] > allowedPages[i-1]+1)||(i===0 && allowedPages[i]!=1)) {
                  this._pageMissingElements.push('page_missing_explanation_' + allowedPages[i].toString());
              }
          }
          if (this._maximumAllowedPage!=this.originalPageCount) {
              this._pageMissingElements.push('page_missing_explanation_' + (this.originalPageCount+1).toString());
          }
      };

      DocumentManager.prototype.minimumPageNumber = function() {
          if (this.viewMode() == 'book') {
            return 0;
          } else {
            return 1;
          }
      };

      DocumentManager.prototype.maximumPageNumber = function() {
          if (this.allowedPages) {
              return this.originalPageCount;
          } else {
              return this.pageCount();
          }
      };

      DocumentManager.prototype.getClosestPageNumber = function(pageNum, direction) {
          if (this.allowedPages) {
              if (this._allowedPagesHash[pageNum]) {
                  return pageNum;
              } else {
                  if (pageNum >= this._maximumAllowedPage) {
                      return this._maximumAllowedPage;
                  } else if (pageNum <= this._minimumAllowedPage) {
                      return this._minimumAllowedPage;
                  }

                  for (var i=1; i <= this.originalPageCount; i++) {
                      if (direction <= 0 &&
                          this._allowedPagesHash[pageNum-i] === true) {
                          return pageNum-i;
                      } else if (
                          direction >=0 &&
                          pageNum + i < this.originalPageCount &&
                          this._allowedPagesHash[pageNum+i] === true) {
                          return pageNum+i;
                      }
                  }
              }
          } else {
              return pageNum;
          }
      };

      DocumentManager.prototype.setPageMissingModulesVisible = function (visible) {
          if (typeof $ === 'undefined' && typeof scribd !== "undefined" ) {
            DocumentManager.setJQuery(scribd.jQuery);
          }
          if (!this._isPaidDocument) {
              return;
          }
          for (var i = 0; i < this._pageMissingElements.length; i++) {
            var elm = $(this._pageMissingElements[i]);
            if (elm) {
              if (visible){
                elm.show();
              } else {
                elm.hide();
              }
            }
          }
      };


      DocumentManager.prototype.getNextAvailablePage = function(pageNum) {
          return getClosestPageNumber(pageNum, 1);
      };

      DocumentManager.prototype.getPreviousAvailablePage = function(pageNum) {
          return getClosestPageNumber(pageNum, -1);
      };

      DocumentManager.prototype.flushFontQueue = function () {
        this._fontLoader.flushFontQueue();
      };


      // Only the ViewManager should call this
      DocumentManager.prototype.visiblePagesChanged = function () {
        var visiblePages = [];
        for (var p in this.pages) {
          if (this.pages.hasOwnProperty(p)) {
            var page = this.pages[p];
            if (page.isVisible) {
              visiblePages.push(page);
            }
          }
        }

        //Gotta sort them
        visiblePages.sort(function(a,b) {
            if (a.pageNum < b.pageNum) {
              return -1;
            } else {
              return 1;
            }
          }
        );

        this.visiblePages = visiblePages;
        var lastFirstVisiblePage = this.firstVisiblePage;
        this.firstVisiblePage = visiblePages.length > 0 ? visiblePages[0] : null;
        this.lastVisiblePage = visiblePages.length > 0 ? visiblePages[visiblePages.length - 1] : null;


        if (!this.isScrolling) {
          this._loadAdjacentFonts();
          this._loadAdjacentPages();
        }

        // Check to see if the first page changed
        if ((this.firstVisiblePage !== lastFirstVisiblePage &&
            (!this.firstVisiblePage || !lastFirstVisiblePage)) ||
          this.firstVisiblePage.pageNum != lastFirstVisiblePage.pageNum) {

          // We don't want to fire this if we're scrolling
          if (!this.isScrolling && this.firstVisiblePage) {
            this._updateExpectedFirstPage(this.firstVisiblePage.pageNum);
          }
        }

        this.scheduleLogPageView();
      };


      function constrain(num, min, max) {
        return Math.min(max, Math.max(min, num));
      }

      DocumentManager.prototype.boundingRatioForPage = function (page) {
        var vpr = this.viewportManager.viewRect; // Make it shorter :P
        var br = page.boundingRect;  // Our bounding rect

        var pageHeight = br.bottom - br.top;
        var pageWidth = br.right - br.left;

        return {
          left: (vpr.left - br.left) / pageWidth,
          right: (vpr.right - br.right) / pageWidth + 1.0,
          'top': constrain((vpr.top - br.top) / pageHeight + page.pageNum,
            page.pageNum,
            page.pageNum + 1.0),
          bottom: constrain((vpr.bottom - br.bottom) / pageHeight + page.pageNum + 1.0,
            page.pageNum,
            page.pageNum + 1.0)
        };
      };


      // Set a timer to log the page view in a second
      // If there's one already scheduled, defer it
      DocumentManager.prototype.scheduleLogPageView = function() {
        if (this.logPageViewTimout) {
          window.clearTimeout(this.logPageViewTimout);

        }
        var self = this;
        this.logPageViewTimout = window.setTimeout(function () {
            self.logPageView();
            self.logPageViewTimout = null;
          },
          1000
        );
      };

      // Rounds to two decimal places
      function _floor2(x) {
        return Math.floor(x * 100.0) / 100.0;
      }

      DocumentManager.prototype.getVisibleBBox = function () {
        var ret = {};
        if (this.firstVisiblePage) {
          var topVb = this.boundingRatioForPage(this.firstVisiblePage);
          ret.left = topVb.left;
          ret.right = topVb.right;
          ret.top = topVb.top;
        }

        if (this.lastVisiblePage) {
          var bottomVb = this.boundingRatioForPage(this.lastVisiblePage);
          ret.bottom = bottomVb.bottom;
        }
        return ret;
      };

      DocumentManager.prototype.logPageView = function()  {
        var bbox = this.getVisibleBBox();

        // Truncate the values to make it a little smaller
        for (var k in bbox) {
          if (bbox.hasOwnProperty(k)) {
            bbox[k] = _floor2(bbox[k]);
          }
        }

        var rat = window.$rat;
        if (rat) {
          var val;
          if (window.RAT_API_VERSION == '2') {
            val = [[bbox.left, bbox.top], [bbox.right, bbox.bottom]];
          } else {
            val =  '(' + bbox.left + ' ' + bbox.top + ') (' + bbox.right + ' ' + bbox.bottom + ')';
          }
          rat('fourgen.viewchange', val);
        }

        this.fireEvent('pageView');
        return bbox;
      };

      DocumentManager.prototype._updateExpectedFirstPage = function (pageNum) {
        this._expectedFirstPageNum = pageNum;
        this.fireEvent('expectedFirstPageChanged', this._expectedFirstPageNum);
      };

      DocumentManager.prototype._loadAdjacentFonts = function () {
        if (this.firstVisiblePage && this.lastVisiblePage) {
          var pagesToDisplay = [];
          var firstLoadPageNum = this.firstVisiblePage.pageNum - adjacentFontLoadPages;
          var lastLoadPageNum = this.lastVisiblePage.pageNum + adjacentFontLoadPages;

          // Some of these will be invalid page numbers, but we check
          for (var i = firstLoadPageNum; i <= lastLoadPageNum; i++) {
            var page = this.pages[i];
            if (page) {
              page.loadFonts();
            }
          }
        }
      };

      DocumentManager.prototype._loadAdjacentPages = function () {
        if (this.firstVisiblePage && this.lastVisiblePage) {
          var pagesToDisplay = [];
          var firstLoadPageNum = this.firstVisiblePage.pageNum - adjacentLoadPages;
          var lastLoadPageNum = this.lastVisiblePage.pageNum + adjacentLoadPages;

          // Some of these will be invalid page numbers, but we check
          for (var i = firstLoadPageNum; i <= lastLoadPageNum; i++) {
            var page = this.pages[i];
            if (page &&!page.loadHasStarted) {
              page.load();
              if (this.mobile) {
                page.setWidth(this._pageWidths);
              }
            }
          }

          if (this.mobile) {
            this._removeUnusedPages();
          }
        }
      };

      // A dirty dirty hack to remove pages outside the scope of the current load window from the DOM
      // This will "hopefully" remedy the crashing issues currently presenting themselves on the iPad
      DocumentManager.prototype._removeUnusedPages = function() {
        var firstLoadPageNum = this.firstVisiblePage.pageNum - adjacentLoadPages;
        var lastLoadPageNum = this.lastVisiblePage.pageNum + adjacentLoadPages;
        var pages = this.pages;

        var i = adjacentLoadPages+1;
        while (pages[i]) {
          if (i < firstLoadPageNum || i > lastLoadPageNum) {
            pages[i].remove();
          }
          i++;
        }

      };

      // ONLY call this after all the outer pages are loaded
      // and after all the elements are zoomed
      DocumentManager.prototype._updatePageBoundingRects = function () {
        for(var p in this.pages) {
          if (this.pages.hasOwnProperty(p)) {
            this.pages[p]._updateBoundingRect();
          }
        }
      };

      // Add a page.  We will be injecting docManager into params, so it will be mutated
      DocumentManager.prototype.addPage = function (params) {
        if (params.pageNum === undefined) {
          throw "must have pageNum param";
        }
        params.docManager = this;

        var page = new Page(params);

        this.pages[params.pageNum] = page;
        if (this._pageWidths) {
          page.setWidth(this._pageWidths);
        }

        if (this.currentFontGroup.isFull()) {
          this.currentFontGroup = this.currentFontGroup.newNextGroup();
        }

        page.setLoadFontGroup(this.currentFontGroup);

        return page;
      };


      // Set isScrolling to true to suppress scroll events if we're
      // forcing the window to scroll
      //
      // It does not automatically load pages while in scrolling mode either
      // Track this re-entrant-ly, using a counter for the number of scroll
      // animations that are still happening.
      DocumentManager.prototype.setIsScrolling = function (isScrolling) {
        // Increment or decrement the counter.
        if (isScrolling) {
          this._scrollingCount += 1;
        } else {
          this._scrollingCount -= 1;
        }
        // Ignore excessive decrements.
        if (this._scrollingCount < 0) {
          this._scrollingCount = 0;
        }
        // Set the boolean variable based on the counter.
        if (this._scrollingCount === 0) {
          this.isScrolling = false;
        } else {
          this.isScrolling = true;
        }
      };

      DocumentManager.prototype.setViewManager = function (viewManagerName, cb) {
        if (this._currentViewManager) {
          this._setViewManager(viewManagerName);
          if(typeof(cb) === 'function') {
            cb();
          }
        }
        else {
          var self = this;
          this.addEvent("viewmodeInitialized", function() {
            self.setViewManager(viewManagerName, cb);
          });
        }
      };

      DocumentManager.prototype._setViewManager = function (viewManagerName, initial) {
        if(!initial) {
          this._currentViewManager.unregister();
        }

        var previousViewManager = this._currentViewManager;
        this._currentViewManager = this.viewManagers[viewManagerName];

        this._currentViewManager.register(this, this.viewportManager);

        this.fireEvent('viewmodeChanged',
         this.viewMode(),
         previousViewManager ? previousViewManager.name() : null);
      };

      DocumentManager.prototype.setInitialViewManager = function (viewManagerName) {
        if (this._currentViewManager) {
          throw "This should be called before any view manager exists";
        }
        this._setViewManager(viewManagerName, true);
        this.fireEvent("viewmodeInitialized", this.viewMode(), null);
      };

      DocumentManager.prototype.setDefaultWidth = function(width) {
          this._currentViewManager._currentPageWidth = width;
          this._currentViewManager._currentZoomMultiplier = 1.0;
          this._currentViewManager._updatePageWidths();
      };

      // Replaces the image src with a domain of our chosing for image loading
      DocumentManager.prototype.subImageSrc = function (src) {

        var i,j = 0;
        // poor man's hash function- we only have four buckets.
        for(i=0;i<src.length;i++) {
          j += src.charCodeAt(i);
        }
        var toDomain = this._imageDomainSubstitutionList[j % this._imageDomainSubstitutionList.length];

        return src.replace(this._imageDomainSubstitutionFrom, toDomain);

      };

      // Call this after the last page is added
      DocumentManager.prototype.allPagesAdded = function () {
        if (this._allPagesAddedCalled) {
          throw "can only call allPagesAdded once";
        }

        this.viewportManager.enable();

        this._updatePageBoundingRects();

        this.setInitialViewManager(this.defaultViewMode);
        this.fireEvent('allPagesAdded');
      };

      // whether or not it is an embed doc.
      DocumentManager.prototype.setEmbeddedDoc = function(isEmbed) {
        this._isEmbed = (isEmbed === 'True');
      };

      // This sets the width of the current page.
      // It also sets the default width of any page that is added
      // When a new page is added, it will be set to the width
      //
      // NOTE: If we have a ZoomManager we probably won't call this directly
      DocumentManager.prototype.setPageWidths = function (width) {
        this._pageWidths = width;
        for(var p in this.pages) {
          if (this.pages.hasOwnProperty(p)) {
            this.pages[p].setWidth(this._pageWidths);
          }
        }
        this._updatePageBoundingRects();
      };

      /////////////////////////
      // Delegate for fontLoader
      ///////////////////////////
      //
      DocumentManager.prototype.addFont = function (id, shortstyle, family, fallback, weight, style) {
        this._fontLoader.addFont(id, shortstyle, family, fallback, weight, style);
      };

      /* deprecated */
      DocumentManager.prototype.setNumFonts = function (numFonts) {
        this._fontLoader.setNumFonts(numFonts);
      };


      DocumentManager.prototype.initStyles = function () {
        this._fontLoader.initStyles();
      };


      //
      // Delegated to View Manager
      //
      DocumentManager.prototype.gotoPage = function(pageId, options) {
        var pageIsFloat = !isInt(pageId);
        var frac = null;

        if(pageIsFloat) {
          frac = +(pageId % 1).toFixed(2);
          pageId = Math.floor(pageId);
        }

        // Abort if we try to go to an illegal page.
        if (pageId < this.minimumPageNumber() ||
            pageId > this.maximumPageNumber()) {
          return;
        }

        if(!options) {
          options = {};
        }
        if (options.pretty === undefined) {
          options.pretty = true;
        }

        if(pageIsFloat && options.frac == undefined)
          options.frac = frac;

        var direction = options.direction || 0;


        var page = this.pages[pageId];
        if (page === undefined && this._isPaidDocument) {
            pageId = this.getClosestPageNumber(pageId,direction);
            page = this.pages[pageId];
        }

        if (this.mobile) {
          if (this.pages[pageId]) {
            this.pages[pageId].setWidth(this._pageWidths);
          }
        }
        this._updateExpectedFirstPage(pageId);
        this._currentViewManager.gotoPage(this._expectedFirstPageNum, options);
      };

      DocumentManager.prototype.gotoPreviousPage = function() {
        var step = this._currentViewManager._pagingStep();
        if (this._currentViewManager.isTopPageInView()) {
          this.gotoPage(this._expectedFirstPageNum - step, {'direction' : -1});
        } else {
          this.gotoPage(this._expectedFirstPageNum, {'direction' : -1});
        }
      };

      DocumentManager.prototype.gotoNextPage = function() {
        var step = this._currentViewManager._pagingStep();
        this.gotoPage(this._expectedFirstPageNum + step, {'direction' : 1});
      };

      DocumentManager.prototype.enterFullscreen = function() {
        this._currentViewManager.enterFullscreen();
      };

      DocumentManager.prototype.exitFullscreen = function() {
        this._currentViewManager.exitFullscreen();
      };

      // {entered|exited}Fullscreen exist on DocumentManager so they can be used from the UI. However,
      // they must be fired from the ViewManager.  So we have these private functions.

      DocumentManager.prototype._fireEnteredFullscreen = function() {
        this.fireEvent('enteredFullscreen');
      };

      DocumentManager.prototype._fireExitedFullscreen = function() {
        this.fireEvent('exitedFullscreen');
      };

      DocumentManager.prototype.viewMode = function() {
        if (this._currentViewManager) {
            return this._currentViewManager.name();
        }
        return null;
      };

      DocumentManager.prototype.zoom = function(multiplier) {
        this._currentViewManager.zoom(multiplier);
      };

      DocumentManager.prototype.resetZoom = function() {
        this._currentViewManager.resetZoom();
      };

      DocumentManager.prototype.setImageDomainSubstitution = function (fromDomain, toList) {
        this._imageDomainSubstitutionFrom = fromDomain;
        this._imageDomainSubstitutionList = toList;
      };

      DocumentManager.prototype.disableViewManagerResizeWidth = function() {
          ViewManager.prototype._checkBodyWidth = function() {};
      };

      DocumentManager.prototype.disable = function() {
          if ( !this.disabled ) {
              this.disabled = true;
              this.viewportManager.disable();
          }
      };

      DocumentManager.setJQuery = function(jQuery) {
        $ = jQuery;
      };

      return DocumentManager;
    })();

  window.DocumentManager = DocumentManager;

  /* vim: set ts=2 sw=2 expandtab */
};

/* only initialize 4gen once */
if(window.DocumentManager === undefined) {
    init_4gen();
}
