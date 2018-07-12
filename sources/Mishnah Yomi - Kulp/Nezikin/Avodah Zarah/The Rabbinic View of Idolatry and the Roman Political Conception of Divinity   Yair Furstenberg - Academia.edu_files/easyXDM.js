/*
 * easyXDM 
 * http://easyxdm.net/
 * Copyright(c) 2009, Øyvind Sean Kinsey, oyvind@kinsey.no.
 * 
 * MIT Licensed - http://easyxdm.net/license/mit.txt
 * 
 */
 (function (window, document, location, setTimeout, decodeURIComponent, encodeURIComponent) {
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, JSON, XMLHttpRequest, window, escape, unescape, ActiveXObject */

var global = this;
var _channelId = 0;
var emptyFn = Function.prototype;
var reURI = /^(http.?:\/\/([^\/\s]+))/, // returns groups for origin (1) and domain (2)
 reParent = /[\-\w]+\/\.\.\//, // matches a foo/../ expression 
 reDoubleSlash = /([^:])\/\//g; // matches // anywhere but in the protocol
//Sniffing is bad, but in this case unavoidable
var CREATE_FRAME_USING_HTML = /msie [67]/.test(navigator.userAgent.toLowerCase());
/* Methods for feature testing
 * From http://peter.michaux.ca/articles/feature-detection-state-of-the-art-browser-scripting
 */
function isHostMethod(object, property){
    var t = typeof object[property];
    return t == 'function' ||
    (!!(t == 'object' && object[property])) ||
    t == 'unknown';
}

function isHostObject(object, property){
    return !!(typeof(object[property]) == 'object' && object[property]);
}

/*
 * Create normalized methods for adding and removing events
 */
var on = (function(){
    if (isHostMethod(window, "addEventListener")) {
        /**
         * Set on to use the DOM level 2 addEventListener
         * https://developer.mozilla.org/en/DOM/element.on
         * @ignore
         * @param {Object} target
         * @param {String} type
         * @param {Function} listener
         */
        return function(target, type, listener){
            target.addEventListener(type, listener, false);
        };
    }
    else {
        /**
         * Set on to a wrapper around the IE spesific attachEvent
         * http://msdn.microsoft.com/en-us/library/ms536343%28VS.85%29.aspx
         * @ignore
         * @param {Object} object
         * @param {String} sEvent
         * @param {Function} fpNotify
         */
        return function(object, sEvent, fpNotify){
            object.attachEvent("on" + sEvent, fpNotify);
        };
    }
}());

var un = (function(){
    if (isHostMethod(window, "removeEventListener")) {
        /**
         * Set un to use the DOM level 2 removeEventListener
         * https://developer.mozilla.org/en/DOM/element.un
         * @ignore
         * @param {Object} target
         * @param {String} type
         * @param {Function} listener
         */
        return function(target, type, listener, useCapture){
            target.removeEventListener(type, listener, useCapture);
        };
    }
    else {
        /**
         * Set un to a wrapper around the IE spesific detachEvent
         * http://msdn.microsoft.com/en-us/library/ms536411%28VS.85%29.aspx
         * @ignore
         * @param {Object} object
         * @param {String} sEvent
         * @param {Function} fpNotify
         */
        return function(object, sEvent, fpNotify){
            object.detachEvent("on" + sEvent, fpNotify);
        };
    }
}());

/*
 * Methods for working with URLs
 */
/**
 * Get the domain name from a url.
 * @private
 * @param {String} url The url to extract the domain from.
 * @returns The domain part of the url.
 * @type {String}
 */
function getDomainName(url){
    return url.match(reURI)[2];
}

/**
 * Returns  a string containing the schema, domain and if present the port
 * @private
 * @param {String} url The url to extract the location from
 * @return {String} The location part of the url
 */
function getLocation(url){
    return url.match(reURI)[1];
}

/**
 * Resolves a relative url into an absolute one.
 * @private
 * @param {String} url The path to resolve.
 * @return {String} The resolved url.
 */
function resolveUrl(url){
    
    // replace all // except the one in proto with /
    url = url.replace(reDoubleSlash, "$1/");
    
    // If the url is a valid url we do nothing
    if (!url.match(/^(http||https):\/\//)) {
        // If this is a relative path
        var path = (url.substring(0, 1) === "/") ? "" : location.pathname;
        if (path.substring(path.length - 1) !== "/") {
            path = path.substring(0, path.lastIndexOf("/") + 1);
        }
        
        url = location.protocol + "//" + location.host + path + url;
    }
    
    // reduce all 'xyz/../' to just '' 
    while (reParent.test(url)) {
        url = url.replace(reParent, "");
    }
    
    return url;
}

/**
 * Appends the parameters to the given url.<br/>
 * The base url can contain existing query parameters.
 * @private
 * @param {String} url The base url.
 * @param {Object} parameters The parameters to add.
 * @return {String} A new valid url with the parameters appended.
 */
function appendQueryParameters(url, parameters){
    
    var hash = "", indexOf = url.indexOf("#");
    if (indexOf !== -1) {
        hash = url.substring(indexOf);
        url = url.substring(0, indexOf);
    }
    var q = [];
    for (var key in parameters) {
        if (parameters.hasOwnProperty(key)) {
            q.push(key + "=" + parameters[key]);
        }
    }
    return url + ((url.indexOf("?") === -1) ? "?" : "&") + q.join("&") + hash;
}

var _query = (function(){
    var query = {}, pair, search = location.search.substring(1).split("&"), i = search.length;
    while (i--) {
        pair = search[i].split("=");
        query[pair[0]] = pair[1];
    }
    return query;
}());

/*
 * Helper methods
 */
/**
 * Helper for checking if a variable/property is undefined
 * @private
 * @param {Object} v The variable to test
 * @return {Boolean} True if the passed variable is undefined
 */
function undef(v){
    return typeof v === "undefined";
}

/**
 * A safe implementation of HTML5 JSON. Feature testing is used to make sure the implementation works.
 * @private
 * @return {JSON} A valid JSON conforming object, or null if not found.
 */
function getJSON(){
    var cached = {};
    var obj = {
        a: [1, 2, 3]
    }, json = "{\"a\":[1,2,3]}";
    
    if (JSON && typeof JSON.stringify === "function" && JSON.stringify(obj).replace((/\s/g), "") === json) {
        // this is a working JSON instance
        return JSON;
    }
    if (Object.toJSON) {
        if (Object.toJSON(obj).replace((/\s/g), "") === json) {
            // this is a working stringify method
            cached.stringify = Object.toJSON;
        }
    }
    
    if (typeof String.prototype.evalJSON === "function") {
        obj = json.evalJSON();
        if (obj.a && obj.a.length === 3 && obj.a[2] === 3) {
            // this is a working parse method           
            cached.parse = function(str){
                return str.evalJSON();
            };
        }
    }
    
    if (cached.stringify && cached.parse) {
        // Only memoize the result if we have valid instance
        getJSON = function(){
            return cached;
        };
        return cached;
    }
    return null;
}

/**
 * Applies properties from the source object to the target object.<br/>
 * This is a destructive method.
 * @private
 * @param {Object} target The target of the properties.
 * @param {Object} source The source of the properties.
 * @param {Boolean} noOverwrite Set to True to only set non-existing properties.
 */
function apply(destination, source, noOverwrite){
    var member;
    for (var prop in source) {
        if (source.hasOwnProperty(prop)) {
            if (prop in destination) {
                member = source[prop];
                if (typeof member === "object") {
                    apply(destination[prop], member, noOverwrite);
                }
                else if (!noOverwrite) {
                    destination[prop] = source[prop];
                }
            }
            else {
                destination[prop] = source[prop];
            }
        }
    }
    return destination;
}

/**
 * Creates a frame and appends it to the DOM.
 * @private
 * @cfg {Object} prop The properties that should be set on the frame. This should include the 'src' property
 * @cfg {Object} attr The attributes that should be set on the frame.
 * @cfg {DOMElement} container Its parent element (Optional)
 * @cfg {Function} onLoad A method that should be called with the frames contentWindow as argument when the frame is fully loaded. (Optional)
 * @return The frames DOMElement
 * @type DOMElement
 */
function createFrame(config){
    var frame;
    // This is to work around the problems in IE6/7 with setting the name property. 
    // Internally this is set as 'submitName' instead when using 'iframe.name = ...'
    // This is not required by easyXDM itself, but is to facilitate other use cases 
    if (config.props.name && CREATE_FRAME_USING_HTML) {
        frame = document.createElement("<iframe name=\"" + config.props.name + "\"/>");
    }
    else {
        frame = document.createElement("IFRAME");
    }
    // transfer properties to the frame
    apply(frame, config.props);
    //id needs to be set for the references to work reliably
    frame.id = frame.name;
    
    if (config.onLoad) {
        frame.loadFn = function(){
            config.onLoad(frame.contentWindow);
        };
        on(frame, "load", frame.loadFn);
    }
    if (config.container) {
        // Remove the frame
        frame.border = frame.frameBorder = 0;
        config.container.appendChild(frame);
    }
    else {
        // This needs to be hidden like this, simply setting display:none and the like will cause failures in some browsers.
        frame.style.position = "absolute";
        frame.style.left = "-2000px";
        frame.style.top = "0px";
        document.body.appendChild(frame);
    }
    return frame;
}

/*
 * Methods related to AJAX
 */
/**
 * Creates a cross-browser XMLHttpRequest object
 * @private
 * @return {XMLHttpRequest} A XMLHttpRequest object.
 */
var getXhr = (function(){
    if (isHostMethod(window, "XMLHttpRequest")) {
        return function(){
            return new XMLHttpRequest();
        };
    }
    else {
        var item = (function(){
            var list = ["Microsoft", "Msxml2", "Msxml3"], i = list.length;
            while (i--) {
                try {
                    item = list[i] + ".XMLHTTP";
                    var obj = new ActiveXObject(item);
                    return item;
                } 
                catch (e) {
                }
            }
        }());
        return function(){
            return new ActiveXObject(item);
        };
    }
}());

/** Runs an asynchronous request using XMLHttpRequest
 * @private
 * @cfg {String} method POST, HEAD or GET
 * @cfg {String} url The url to request
 * @cfg {Object} data Any data that should be sent.
 * @cfg {Function} success The callback function for successfull requests
 * @cfg {Function} error The callback function for errors
 */
function ajax(config){
    apply(config, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest"
        },
        success: emptyFn,
        error: function(msg){
            throw new Error(msg);
        },
        data: {},
        type: "plain"
    }, true);
    
    var req = getXhr(), q = [];
    req.open(config.method, config.url, true);
    for (var prop in config.headers) {
        if (config.headers.hasOwnProperty(prop)) {
            req.setRequestHeader(prop, config.headers[prop]);
        }
    }
    
    req.onreadystatechange = function(){
        if (req.readyState == 4) {
            if (req.status >= 200 && req.status < 300) {
                var response = req.responseText;
                if (config.type === "json") {
                    response = getJSON().parse(response);
                }
                config.success(response);
            }
            else {
                config.error("An error occured. Status code: " + req.status);
            }
            req.onreadystatechange = null;
            delete req.onreadystatechange;
        }
    };
    
    for (var key in config.data) {
        if (config.data.hasOwnProperty(key)) {
            q.push(encodeURIComponent(key) + "=" + encodeURIComponent(config.data[key]));
        }
    }
    req.send(q.join("&"));
}

/*
 * Functions related to stacks
 */
/**
 * Prepares an array of stack-elements suitable for the current configuration
 * @private
 * @param {Object} config The Transports configuration. See easyXDM.Socket for more.
 * @return {Array} An array of stack-elements with the TransportElement at index 0.
 */
function prepareTransportStack(config){
    var protocol = config.protocol, stackEls;
    config.isHost = config.isHost || undef(_query.xdm_p);
    
    if (!config.props) {
        config.props = {};
    }
    if (!config.isHost) {
        config.channel = _query.xdm_c;
        config.secret = _query.xdm_s;
        config.remote = decodeURIComponent(_query.xdm_e);
        protocol = _query.xdm_p;
    }
    else {
        config.remote = resolveUrl(config.remote);
        config.channel = config.channel || "default" + _channelId++;
        config.secret = Math.random().toString(16).substring(2);
        if (undef(protocol)) {
            if (isHostMethod(window, "postMessage")) {
                /*
                 * This is supported in IE8+, Firefox 3+, Opera 9+, Chrome 2+ and Safari 4+
                 */
                protocol = "1";
            }
            else if (isHostMethod(window, "ActiveXObject") && isHostMethod(window, "execScript")) {
                /*
                 * This is supported in IE6 and IE7
                 */
                protocol = "3";
            }
            else if (config.remoteHelper) {
                /*
                 * This is supported in all browsers that retains the value of window.name when
                 * navigating from one domain to another, and where parent.frames[foo] can be used
                 * to get access to a frame from the same domain
                 */
                config.remoteHelper = resolveUrl(config.remoteHelper);
                protocol = "2";
            }
            else {
                /*
                 * This is supported in all browsers where [window].location is writable for all
                 * The resize event will be used if resize is supported and the iframe is not put
                 * into a container, else polling will be used.
                 */
                protocol = "0";
            }
        }
    }
    
    switch (protocol) {
        case "0":// 0 = HashTransport
            apply(config, {
                interval: 300,
                delay: 2000,
                useResize: true,
                useParent: false,
                usePolling: false
            }, true);
            if (config.isHost) {
                if (!config.local) {
                    // If no local is set then we need to find an image hosted on the current domain
                    var domain = location.protocol + "//" + location.host, images = document.body.getElementsByTagName("img"), i = images.length, image;
                    while (i--) {
                        image = images[i];
                        if (image.src.substring(0, domain.length) === domain) {
                            config.local = image.src;
                            break;
                        }
                    }
                    if (!config.local) {
                        // If no local was set, and we are unable to find a suitable file, then we resort to using the current window 
                        config.local = window;
                    }
                }
                
                var parameters = {
                    xdm_c: config.channel,
                    xdm_p: 0
                };
                
                if (config.local === window) {
                    // We are using the current window to listen to
                    config.usePolling = true;
                    config.useParent = true;
                    config.local = location.protocol + "//" + location.host + location.pathname + location.search;
                    parameters.xdm_e = encodeURIComponent(config.local);
                    parameters.xdm_pa = 1; // use parent
                }
                else {
                    parameters.xdm_e = resolveUrl(config.local);
                }
                
                if (config.container) {
                    config.useResize = false;
                    parameters.xdm_po = 1; // use polling
                }
                config.remote = appendQueryParameters(config.remote, parameters);
            }
            else {
                apply(config, {
                    channel: _query.xdm_c,
                    remote: decodeURIComponent(_query.xdm_e),
                    useParent: !undef(_query.xdm_pa),
                    usePolling: !undef(_query.xdm_po),
                    useResize: config.useParent ? false : config.useResize
                });
            }
            stackEls = [new easyXDM.stack.HashTransport(config), new easyXDM.stack.ReliableBehavior({
                timeout: ((config.useResize ? 50 : config.interval * 1.5) + (config.usePolling ? config.interval * 1.5 : 50))
            }), new easyXDM.stack.QueueBehavior({
                encode: true,
                maxLength: 4000 - config.remote.length
            }), new easyXDM.stack.VerifyBehavior({
                initiate: config.isHost
            })];
            break;
        case "1":
            stackEls = [new easyXDM.stack.PostMessageTransport(config), new easyXDM.stack.QueueBehavior()];
            break;
        case "2":
            stackEls = [new easyXDM.stack.NameTransport(config), new easyXDM.stack.QueueBehavior(), new easyXDM.stack.VerifyBehavior({
                initiate: config.isHost
            })];
            break;
        case "3":
            stackEls = [new easyXDM.stack.NixTransport(config), new easyXDM.stack.QueueBehavior()];
            break;
    }
    
    return stackEls;
}

/**
 * Chains all the separate stack elements into a single usable stack.<br/>
 * If an element is missing a necessary method then it will have a pass-through method applied.
 * @private
 * @param {Array} stackElements An array of stack elements to be linked.
 * @return {easyXDM.stack.StackElement} The last element in the chain.
 */
function chainStack(stackElements){
    var stackEl, defaults = {
        incoming: function(message, origin){
            this.up.incoming(message, origin);
        },
        outgoing: function(message, recipient){
            this.down.outgoing(message, recipient);
        },
        callback: function(success){
            this.up.callback(success);
        },
        init: function(){
            this.down.init();
        },
        destroy: function(){
            this.down.destroy();
        }
    };
    for (var i = 0, len = stackElements.length; i < len; i++) {
        stackEl = stackElements[i];
        apply(stackEl, defaults, true);
        if (i !== 0) {
            stackEl.down = stackElements[i - 1];
        }
        if (i !== len - 1) {
            stackEl.up = stackElements[i + 1];
        }
    }
    return stackEl;
}

/*
 * Export the main object and any other methods applicable
 */
/** 
 * @class easyXDM
 * A javascript library providing cross-browser, cross-domain messaging/RPC.
 * @version 2.4.0.90
 * @singleton
 */
global.easyXDM = {
    /**
     * The version of the library
     * @type {String}
     */
    version: "2.4.0.90",
    apply: apply,
    query: _query,
    ajax: ajax,
    getJSONObject: getJSON,
    stack: {}
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global console, _FirebugCommandLine,  easyXDM, window, escape, unescape, isHostObject, undef, _trace */

/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, isHostObject, isHostMethod, un, on, createFrame, debug */

/** 
 * @class easyXDM.DomHelper
 * Contains methods for dealing with the DOM
 * @singleton
 */
easyXDM.DomHelper = {
    /**
     * Provides a consistent interface for adding eventhandlers
     * @param {Object} target The target to add the event to
     * @param {String} type The name of the event
     * @param {Function} listener The listener
     */
    on: on,
    /**
     * Provides a consistent interface for removing eventhandlers
     * @param {Object} target The target to remove the event from
     * @param {String} type The name of the event
     * @param {Function} listener The listener
     */
    un: un,
    /**
     * Checks for the presence of the JSON object.
     * If it is not present it will use the supplied path to load the JSON2 library.
     * This should be called in the documents head right after the easyXDM script tag.
     * http://json.org/json2.js
     * @param {String} path A valid path to json2.js
     */
    requiresJSON: function(path){
        if (!isHostObject(window, "JSON")) {
            document.write('<script type="text/javascript" src="' + path + '"></script>');
        }
    }
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, debug */


(function(){
    // The map containing the stored functions
    var _map = {};
    
    /**
     * @class easyXDM.Fn
     * This contains methods related to function handling, such as storing callbacks.
     * @singleton
     * @namespace easyXDM
     */
    easyXDM.Fn = {
        /**
         * Stores a function using the given name for reference
         * @param {String} name The name that the function should be referred by
         * @param {Function} fn The function to store
         * @namespace easyXDM.fn
         */
        set: function(name, fn){
            _map[name] = fn;
        },
        /**
         * Retrieves the function referred to by the given name
         * @param {String} name The name of the function to retrieve
         * @param {Boolean} del If the function should be deleted after retrieval
         * @return {Function} The stored function
         * @namespace easyXDM.fn
         */
        get: function(name, del){
            var fn = _map[name];
            
            if (del) {
                delete _map[name];
            }
            return fn;
        }
    };
    
}());
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, chainStack, prepareTransportStack, getLocation, debug */

/**
 * @class easyXDM.Socket
 * This class creates a transport channel between two domains that is usable for sending and receiving string-based messages.<br/>
 * The channel is reliable, supports queueing, and ensures that the message originates from the expected domain.<br/>
 * Internally different stacks will be used depending on the browsers features and the available parameters.
 * <h2>How to set up</h2>
 * Setting up the provider:
 * <pre><code>
 * var socket = new easyXDM.Socket({
 * &nbsp; local: "name.html",
 * &nbsp; onReady: function(){
 * &nbsp; &nbsp; &#47;&#47; you need to wait for the onReady callback before using the socket
 * &nbsp; &nbsp; socket.postMessage("foo-message");
 * &nbsp; },
 * &nbsp; onMessage: function(message, origin) {
 * &nbsp;&nbsp; alert("received " + message + " from " + origin);
 * &nbsp; }
 * });
 * </code></pre>
 * Setting up the consumer:
 * <pre><code>
 * var socket = new easyXDM.Socket({
 * &nbsp; remote: "http:&#47;&#47;remotedomain/page.html",
 * &nbsp; remoteHelper: "http:&#47;&#47;remotedomain/name.html",
 * &nbsp; onReady: function(){
 * &nbsp; &nbsp; &#47;&#47; you need to wait for the onReady callback before using the socket
 * &nbsp; &nbsp; socket.postMessage("foo-message");
 * &nbsp; },
 * &nbsp; onMessage: function(message, origin) {
 * &nbsp;&nbsp; alert("received " + message + " from " + origin);
 * &nbsp; }
 * });
 * </code></pre>
 * If you are unable to upload the <code>name.html</code> file to the consumers domain then remove <code>removeHelper</code> property
 * and the transport will fall back to using FMI instead of the window.name to transport messages.
 * @namespace easyXDM
 * @constructor
 * @cfg {String/Window} local The url to the local name.html document, a local static file, or a reference to the local window.
 * @cfg {String} remote The url to the providers document.
 * @cfg {String} remoteHelper The url to the remote name.html file. This is to support NameTransport as a fallback. Optional.
 * @cfg {Number} delay The number of milliseconds easyXDM should try to get a reference to the local window.  Optional, defaults to 2000.
 * @cfg {Number} interval The interval used when polling for messages. Optional, defaults to 300.
 * @cfg {String} channel The name of the channel to use. Must be unique. Optional if only a single channel is expected in the document.
 * @cfg {Function} onMessage The method that should handle incoming messages.<br/> This method should accept two arguments, the message as a string, and the origin as a string. Optional.
 * @cfg {Function} onReady A method that should be called when the transport is ready. Optional.
 * @cfg {DOMElement} container The element that the primary iframe should be inserted into. If not set then the iframe will be positioned off-screen. Optional.
 * @cfg {Object} props Additional properties that should be applied to the iframe. This can also contain nested objects e.g: <code>{style:{width:"100px", height:"100px"}}</code>. 
 * Properties such as 'name' and 'src' will be overrided. Optional.
 */
easyXDM.Socket = function(config){
    
    var stack = chainStack(prepareTransportStack(config).concat([{
        incoming: function(message, origin){
            config.onMessage(message, origin);
        },
        callback: function(success){
            if (config.onReady) {
                config.onReady(success);
            }
        }
    }])), recipient = getLocation(config.remote);
    
    /**
     * Initiates the destruction of the stack.
     */
    this.destroy = function(){
        stack.destroy();
    };
    
    /**
     * Posts a message to the remote end of the channel
     * @param {String} message The message to send
     */
    this.postMessage = function(message){
        stack.outgoing(message, recipient);
    };
    
    stack.init();
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, undef,, chainStack, prepareTransportStack, debug */

/** 
 * @class easyXDM.Rpc
 * Creates a proxy object that can be used to call methods implemented on the remote end of the channel, and also to provide the implementation
 * of methods to be called from the remote end.<br/>
 * The instantiated object will have methods matching those specified in <code>config.remote</code>.<br/>
 * This requires the JSON object present in the document, either natively, using json.org's json2 or as a wrapper around library spesific methods.
 * <h2>How to set up</h2>
 * <pre><code>
 * var rpc = new easyXDM.Rpc({
 * &nbsp; &#47;&#47; this configuration is equal to that used by the Socket.
 * &nbsp; remote: "http:&#47;&#47;remotedomain/...",
 * &nbsp; onReady: function(){
 * &nbsp; &nbsp; &#47;&#47; you need to wait for the onReady callback before using the proxy
 * &nbsp; &nbsp; rpc.foo(...
 * &nbsp; }
 * },{
 * &nbsp; local: {..},
 * &nbsp; remote: {..}
 * });
 * </code></pre>
 * 
 * <h2>Exposing functions (procedures)</h2>
 * <pre><code>
 * var rpc = new easyXDM.Rpc({
 * &nbsp; ...
 * },{
 * &nbsp; local: {
 * &nbsp; &nbsp; nameOfMethod: {
 * &nbsp; &nbsp; &nbsp; method: function(arg1, arg2, success, error){
 * &nbsp; &nbsp; &nbsp; &nbsp; ...
 * &nbsp; &nbsp; &nbsp; }
 * &nbsp; &nbsp; },
 * &nbsp; &nbsp; &#47;&#47; with shorthand notation 
 * &nbsp; &nbsp; nameOfAnotherMethod:  function(arg1, arg2, success, error){
 * &nbsp; &nbsp; }
 * &nbsp; },
 * &nbsp; remote: {...}
 * });
 * </code></pre>

 * The function referenced by  [method] will receive the passed arguments followed by the callback functions <code>success</code> and <code>error</code>.<br/>
 * To send a successfull result back you can use
 *     <pre><code>
 *     return foo;
 *     </pre></code>
 * or
 *     <pre><code>
 *     success(foo);
 *     </pre></code>
 *  To return an error you can use
 *     <pre><code>
 *     throw new Error("foo error");
 *     </code></pre>
 * or
 *     <pre><code>
 *     error("foo error");
 *     </code></pre>
 *
 * <h2>Defining remotely exposed methods (procedures/notifications)</h2>
 * The definition of the remote end is quite similar:
 * <pre><code>
 * var rpc = new easyXDM.Rpc({
 * &nbsp; ...
 * },{
 * &nbsp; local: {...},
 * &nbsp; remote: {
 * &nbsp; &nbsp; nameOfMethod: {}
 * &nbsp; }
 * });
 * </code></pre>
 * To call a remote method use
 * <pre><code>
 * rpc.nameOfMethod("arg1", "arg2", function(value) {
 * &nbsp; alert("success: " + value);
 * }, function(message) {
 * &nbsp; alert("error: " + message + );
 * });
 * </code></pre>
 * Both the <code>success</code> and <code>errror</code> callbacks are optional.<br/>
 * When called with no callback a JSON-RPC 2.0 notification will be executed.
 * Be aware that you will not be notified of any errors with this method.
 * <br/>
 * <h2>Specifying a custom serializer</h2>
 * If you do not want to use the JSON2 library for non-native JSON support, but instead capabilities provided by some other library
 * then you can specify a custom serializer using <code>serializer: foo</code>
 * <pre><code>
 * var rpc = new easyXDM.Rpc({
 * &nbsp; ...
 * },{
 * &nbsp; local: {...},
 * &nbsp; remote: {...},
 * &nbsp; serializer : {
 * &nbsp; &nbsp; parse: function(string){ ... },
 * &nbsp; &nbsp; stringify: function(object) {...}
 * &nbsp; }
 * });
 * </code></pre>
 * If <code>serializer</code> is set then the class will not attempt to use the native implementation.
 * @namespace easyXDM
 * @constructor
 * @param {Object} config The underlying transports configuration. See easyXDM.Socket for available parameters.
 * @param {Object} jsonRpcConfig The description of the interface to implement.
 */
easyXDM.Rpc = function(config, jsonRpcConfig){
    
    // expand shorthand notation
    if (jsonRpcConfig.local) {
        for (var method in jsonRpcConfig.local) {
            if (jsonRpcConfig.local.hasOwnProperty(method)) {
                var member = jsonRpcConfig.local[method];
                if (typeof member === "function") {
                    jsonRpcConfig.local[method] = {
                        method: member
                    };
                }
            }
        }
    }
    var stack = chainStack(prepareTransportStack(config).concat([new easyXDM.stack.RpcBehavior(this, jsonRpcConfig), {
        callback: function(success){
            if (config.onReady) {
                config.onReady(success);
            }
        }
    }]));
    
    /**
     * Initiates the destruction of the stack.
     */
    this.destroy = function(){
        stack.destroy();
    };
    
    stack.init();
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, getLocation, appendQueryParameters, createFrame, debug, un, on, apply*/

/**
 * @class easyXDM.stack.PostMessageTransport
 * PostMessageTransport is a transport class that uses HTML5 postMessage for communication.<br/>
 * <a href="http://msdn.microsoft.com/en-us/library/ms644944(VS.85).aspx">http://msdn.microsoft.com/en-us/library/ms644944(VS.85).aspx</a><br/>
 * <a href="https://developer.mozilla.org/en/DOM/window.postMessage">https://developer.mozilla.org/en/DOM/window.postMessage</a>
 * @namespace easyXDM.stack
 * @constructor
 * @param {Object} config The transports configuration.
 * @cfg {String} remote The remote domain to communicate with.
 */
easyXDM.stack.PostMessageTransport = function(config){
    var pub, // the public interface
 frame, // the remote frame, if any
 callerWindow, // the window that we will call with
 targetOrigin; // the domain to communicate with
    /**
     * Resolves the origin from the event object
     * @private
     * @param {Object} event The messageevent
     * @return {String} The scheme, host and port of the origin
     */
    function _getOrigin(event){
        if (event.origin) {
            // This is the HTML5 property
            return event.origin;
        }
        if (event.uri) {
            // From earlier implementations 
            return getLocation(event.uri);
        }
        if (event.domain) {
            // This is the last option and will fail if the 
            // origin is not using the same schema as we are
            return location.protocol + "//" + event.domain;
        }
        throw "Unable to retrieve the origin of the event";
    }
    
    /**
     * This is the main implementation for the onMessage event.<br/>
     * It checks the validity of the origin and passes the message on if appropriate.
     * @private
     * @param {Object} event The messageevent
     */
    function _window_onMessage(event){
        var origin = _getOrigin(event);
        if (origin == targetOrigin && event.data.substring(0, config.channel.length + 1) == config.channel + " ") {
            pub.up.incoming(event.data.substring(config.channel.length + 1), origin);
        }
    }
    
    return (pub = {
        outgoing: function(message, domain, fn){
            callerWindow.postMessage(config.channel + " " + message, domain || targetOrigin);
            fn();
        },
        destroy: function(){
            un(window, "message", _window_onMessage);
            if (frame) {
                callerWindow = null;
                frame.parentNode.removeChild(frame);
                frame = null;
            }
        },
        init: function(){
            targetOrigin = getLocation(config.remote);
            if (config.isHost) {
                // add the event handler for listening
                on(window, "message", function waitForReady(event){
                    if (event.data == config.channel + "-ready") {
                        // replace the eventlistener
                        callerWindow = frame.contentWindow;
                        un(window, "message", waitForReady);
                        on(window, "message", _window_onMessage);
                        setTimeout(function(){
                            pub.up.callback(true);
                        }, 0);
                    }
                });
                // set up the iframe
                apply(config.props, {
                    src: appendQueryParameters(config.remote, {
                        xdm_e: location.protocol + "//" + location.host,
                        xdm_c: config.channel,
                        xdm_p: 1 // 1 = PostMessage
                    })
                });
                frame = createFrame(config);
            }
            else {
                // add the event handler for listening
                on(window, "message", _window_onMessage);
                callerWindow = window.parent;
                callerWindow.postMessage(config.channel + "-ready", targetOrigin);
                setTimeout(function(){
                    pub.up.callback(true);
                }, 0);
            }
        }
    });
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global global, GetNixProxy, easyXDM, window, escape, unescape, getLocation, appendQueryParameters, createFrame, debug, un, on, isHostMethod, apply*/

/**
 * @class easyXDM.stack.NixTransport
 * NixTransport is a transport class that uses the strange fact that in IE <8, the window.opener property can be written to and read from all windows.<br/>
 * This is used to pass methods that are able to relay messages back and forth. To avoid context-leakage a VBScript (COM) object is used to relay all the strings.<br/>
 * This transport is loosely based on the work done by <a href="https://issues.apache.org/jira/browse/SHINDIG-416">Shindig</a>
 * @namespace easyXDM.stack
 * @constructor
 * @param {Object} config The transports configuration.
 * @cfg {String} remote The remote domain to communicate with.
 * @cfg {String} secret the pre-shared secret used to secure the communication.
 */
easyXDM.stack.NixTransport = function(config){
    var pub, // the public interface
 frame, send, targetOrigin, proxy;
    
    return (pub = {
        outgoing: function(message, domain, fn){
            send(message);
            fn();
        },
        destroy: function(){
            proxy = null;
            if (frame) {
                frame.parentNode.removeChild(frame);
                frame = null;
            }
        },
        init: function(){
            targetOrigin = getLocation(config.remote);
            if (config.isHost) {
                try {
                    if (!isHostMethod(window, "GetNixProxy")) {
                        window.execScript('Class NixProxy\n' +
                        '    Private m_parent, m_child, m_Auth\n' +
                        '\n' +
                        '    Public Sub SetParent(obj, auth)\n' +
                        '        If isEmpty(m_Auth) Then m_Auth = auth\n' +
                        '        SET m_parent = obj\n' +
                        '    End Sub\n' +
                        '    Public Sub SetChild(obj)\n' +
                        '        SET m_child = obj\n' +
                        '        m_parent.ready()\n' +
                        '    End Sub\n' +
                        '\n' +
                        // The auth string, which is a pre-shared key between the parent and the child, 
                        // and that can only be set once by the parent, secures the communication, and also serves to provide
                        // 'proof' of the origin of the messages.
                        // Before passing the message on to the recipent we convert the message into a primitive, 
                        // this mitigates modifying .toString as an attack vector.
                        '    Public Sub SendToParent(data, auth)\n' +
                        '        If m_Auth = auth Then m_parent.send(CStr(data))\n' +
                        '    End Sub\n' +
                        '    Public Sub SendToChild(data, auth)\n' +
                        '        If m_Auth = auth Then m_child.send(CStr(data))\n' +
                        '    End Sub\n' +
                        'End Class\n' +
                        'Function GetNixProxy()\n' +
                        '    Set GetNixProxy = New NixProxy\n' +
                        'End Function\n', 'vbscript');
                    }
                    proxy = GetNixProxy();
                    proxy.SetParent({
                        send: function(msg){
                            pub.up.incoming(msg, targetOrigin);
                        },
                        ready: function(){
                            setTimeout(function(){
                                pub.up.callback(true);
                            }, 0);
                        }
                    }, config.secret);
                    send = function(msg){
                        proxy.SendToChild(msg, config.secret);
                    };
                } 
                catch (e) {
                    throw new Error("Could not set up VBScript NixProxy:" + e.message);
                }
                // set up the iframe
                apply(config.props, {
                    src: appendQueryParameters(config.remote, {
                        xdm_e: location.protocol + "//" + location.host,
                        xdm_c: config.channel,
                        xdm_s: config.secret,
                        xdm_p: 3 // 3 = NixTransport
                    })
                });
                frame = createFrame(config);
                frame.contentWindow.opener = proxy;
            }
            else {
                // by storing this in a variable we negate replacement attacks
                try {
                    proxy = window.opener;
                } 
                catch (e) {
                    throw new Error("Cannot access window.opener");
                }
                proxy.SetChild({
                    send: function(msg){
                        // the timeout is necessary to have execution continue in the correct context
                        global.setTimeout(function(){
                            pub.up.incoming(msg, targetOrigin);
                        }, 0);
                    }
                });
                
                send = function(msg){
                    proxy.SendToParent(msg, config.secret);
                };
                setTimeout(function(){
                    pub.up.callback(true);
                }, 0);
            }
        }
    });
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, undef, getLocation, appendQueryParameters, resolveUrl, createFrame, debug, un, apply */

/**
 * @class easyXDM.stack.NameTransport
 * NameTransport uses the window.name property to relay data.
 * The <code>local</code> parameter needs to be set on both the consumer and provider,<br/>
 * and the <code>remoteHelper</code> parameter needs to be set on the consumer.
 * @constructor
 * @param {Object} config The transports configuration.
 * @cfg {String} remoteHelper The url to the remote instance of hash.html - this is only needed for the host.
 * @namespace easyXDM.stack
 */
easyXDM.stack.NameTransport = function(config){
    
    var pub; // the public interface
    var isHost, callerWindow, remoteWindow, readyCount, callback, remoteOrigin, remoteUrl;
    
    function _sendMessage(message){
        var url = config.remoteHelper + (isHost ? ("#_3" + encodeURIComponent(remoteUrl + "#" + config.channel)) : ("#_2" + config.channel));
        callerWindow.contentWindow.sendMessage(message, url);
    }
    
    function _onReady(){
        if (isHost) {
            if (++readyCount === 2 || !isHost) {
                pub.up.callback(true);
            }
        }
        else {
            _sendMessage("ready");
            pub.up.callback(true);
        }
    }
    
    function _onMessage(message){
        pub.up.incoming(message, remoteOrigin);
    }
    
    function _onLoad(){
        if (callback) {
            setTimeout(function(){
                callback(true);
            }, 0);
        }
    }
    
    return (pub = {
        outgoing: function(message, domain, fn){
            callback = fn;
            _sendMessage(message);
        },
        destroy: function(){
            callerWindow.parentNode.removeChild(callerWindow);
            callerWindow = null;
            if (isHost) {
                remoteWindow.parentNode.removeChild(remoteWindow);
                remoteWindow = null;
            }
        },
        init: function(){
            isHost = config.isHost;
            readyCount = 0;
            remoteOrigin = getLocation(config.remote);
            config.local = resolveUrl(config.local);
            
            if (isHost) {
                // Register the callback
                easyXDM.Fn.set(config.channel, function(message){
                    if (isHost && message === "ready") {
                        // Replace the handler
                        easyXDM.Fn.set(config.channel, _onMessage);
                        _onReady();
                    }
                });
                
                // Set up the frame that points to the remote instance
                remoteUrl = appendQueryParameters(config.remote, {
                    xdm_e: config.local,
                    xdm_c: config.channel,
                    xdm_p: 2
                });
                apply(config.props, {
                    src: remoteUrl + '#' + config.channel,
                    name: config.channel
                });
                remoteWindow = createFrame(config);
            }
            else {
                config.remoteHelper = config.remote;
                easyXDM.Fn.set(config.channel, _onMessage);
            }
            // Set up the iframe that will be used for the transport
            callerWindow = createFrame({
                props: {
                    src: config.local + "#_4" + config.channel
                },
                onLoad: function(){
                    // Remove the handler
                    un(callerWindow, "load", callerWindow.loadFn);
                    easyXDM.Fn.set(config.channel + "_load", _onLoad);
                    _onReady();
                }
            });
        }
    });
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, getLocation, createFrame, debug, un, on, apply*/

/**
 * @class easyXDM.stack.HashTransport
 * HashTransport is a transport class that uses the IFrame URL Technique for communication.<br/>
 * <a href="http://msdn.microsoft.com/en-us/library/bb735305.aspx">http://msdn.microsoft.com/en-us/library/bb735305.aspx</a><br/>
 * @namespace easyXDM.stack
 * @constructor
 * @param {Object} config The transports configuration.
 * @cfg {String/Window} local The url to the local file used for proxying messages, or the local window.
 * @cfg {Number} delay The number of milliseconds easyXDM should try to get a reference to the local window.
 * @cfg {Number} interval The interval used when polling for messages.
 */
easyXDM.stack.HashTransport = function(config){
    var pub;
    var me = this, isHost, _timer, pollInterval, _lastMsg, _msgNr, _listenerWindow, _callerWindow;
    var usePolling, useParent, useResize, _remoteOrigin;
    
    function _sendMessage(message){
        if (!_callerWindow) {
            return;
        }
        var url = config.remote + "#" + (_msgNr++) + "_" + message;
        
        if (isHost || !useParent) {
            // We are referencing an iframe
            _callerWindow.contentWindow.location = url;
            if (useResize) {
                _callerWindow.width = _callerWindow.width > 75 ? 50 : 100;
            }
        }
        else {
            // We are referencing the parent window
            _callerWindow.location = url;
        }
    }
    
    function _handleHash(hash){
        _lastMsg = hash;
        pub.up.incoming(_lastMsg.substring(_lastMsg.indexOf("_") + 1), _remoteOrigin);
    }
    
    function _onResize(){
        _handleHash(_listenerWindow.location.hash);
    }
    
    /**
     * Checks location.hash for a new message and relays this to the receiver.
     * @private
     */
    function _pollHash(){
        if (_listenerWindow.location.hash && _listenerWindow.location.hash != _lastMsg) {
            _handleHash(_listenerWindow.location.hash);
        }
    }
    
    function _attachListeners(){
        if (usePolling) {
            _timer = setInterval(_pollHash, pollInterval);
        }
        else {
            on(_listenerWindow, "resize", _onResize);
        }
    }
    
    return (pub = {
        outgoing: function(message, domain){
            _sendMessage(message);
        },
        destroy: function(){
            if (usePolling) {
                window.clearInterval(_timer);
            }
            else if (_listenerWindow) {
                un(_listenerWindow, "resize", _pollHash);
            }
            if (isHost || !useParent) {
                _callerWindow.parentNode.removeChild(_callerWindow);
            }
            _callerWindow = null;
        },
        init: function(){
            isHost = config.isHost;
            pollInterval = config.interval;
            _lastMsg = "#" + config.channel;
            _msgNr = 0;
            usePolling = config.usePolling;
            useParent = config.useParent;
            useResize = config.useResize;
            _remoteOrigin = getLocation(config.remote);
            
            if (!isHost && useParent) {
                _listenerWindow = window;
                _callerWindow = parent;
                _attachListeners();
                pub.up.callback(true);
            }
            else {
                apply(config, {
                    props: {
                        src: (isHost ? config.remote : config.remote + "#" + config.channel),
                        name: (isHost ? "local_" : "remote_") + config.channel
                    },
                    onLoad: (isHost && useParent || !isHost) ? (function(){
                        _listenerWindow = window;
                        _attachListeners();
                        pub.up.callback(true);
                    }) : null
                });
                _callerWindow = createFrame(config);
                
                if (isHost && !useParent) {
                    var tries = 0, max = config.delay / 50;
                    (function getRef(){
                        if (++tries > max) {
                            throw new Error("Unable to reference listenerwindow");
                        }
                        if (_listenerWindow) {
                            return;
                        }
                        try {
                            // This works in IE6
                            _listenerWindow = _callerWindow.contentWindow.frames["remote_" + config.channel];
                            window.clearTimeout(_timer);
                            _attachListeners();
                            pub.up.callback(true);
                            return;
                        } 
                        catch (ex) {
                            setTimeout(getRef, 50);
                        }
                    }());
                }
            }
        }
    });
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, debug */

/**
 * @class easyXDM.stack.ReliableBehavior
 * This is a behavior that tries to make the underlying transport reliable by using acknowledgements.
 * @namespace easyXDM.stack
 * @constructor
 * @param {Object} config The behaviors configuration.
 * @cfg {Number} timeout How long it should wait before resending. Default is 5. Optional.
 * @cfg {Number} tries How many times it should try before giving up.
 */
easyXDM.stack.ReliableBehavior = function(config){
    var pub, // the public interface
 timer, // timer to wait for acks
 current, // the current message beging sent
 next, // the next message to be sent, to support piggybacking acks
 sendId = 0, // the id of the last message sent
 sendCount = 0, // how many times we hav tried resending
 maxTries = config.tries || 5, timeout = config.timeout, //
 receiveId = 0, // the id of the last message received
 callback; // the callback to execute when we have a confirmed success/failure
    return (pub = {
        incoming: function(message, origin){
            var indexOf = message.indexOf("_"), ack = parseInt(message.substring(0, indexOf), 10), id;
            message = message.substring(indexOf + 1);
            indexOf = message.indexOf("_");
            id = parseInt(message.substring(0, indexOf), 10);
            indexOf = message.indexOf("_");
            message = message.substring(indexOf + 1);
            if (timer && ack === sendId) {
                window.clearTimeout(timer);
                timer = null;
                if (callback) {
                    setTimeout(function(){
                        callback(true);
                    }, 0);
                }
            }
            if (id !== 0) {
                if (id !== receiveId) {
                    receiveId = id;
                    message = message.substring(id.length + 1);
                    pub.down.outgoing(id + "_0_ack", origin);
                    // we must give the other end time to pick up the ack
                    setTimeout(function(){
                        pub.up.incoming(message, origin);
                    }, config.timeout / 2);
                }
                else {
                    pub.down.outgoing(id + "_0_ack", origin);
                }
            }
        },
        outgoing: function(message, origin, fn){
            callback = fn;
            sendCount = 0;
            current = {
                data: receiveId + "_" + (++sendId) + "_" + message,
                origin: origin
            };
            
            // Keep resending until we have an ack
            (function send(){
                timer = null;
                if (++sendCount > maxTries) {
                    if (callback) {
                        setTimeout(function(){
                            callback(false);
                        }, 0);
                    }
                }
                else {
                    pub.down.outgoing(current.data, current.origin);
                    timer = setTimeout(send, config.timeout);
                }
            }());
        },
        destroy: function(){
            if (timer) {
                window.clearInterval(timer);
            }
            pub.down.destroy();
        }
    });
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, debug, undef*/

/**
 * @class easyXDM.stack.QueueBehavior
 * This is a behavior that enables queueing of messages. <br/>
 * It will buffer incoming messages and dispach these as fast as the underlying transport allows.
 * This will also fragment/defragment messages so that the outgoing message is never bigger than the
 * set length.
 * @namespace easyXDM.stack
 * @constructor
 * @param {Object} config The behaviors configuration. Optional.
 * @cfg {Number} maxLength The maximum length of each outgoing message. Set this to enable fragmentation.
 */
easyXDM.stack.QueueBehavior = function(config){
    var pub, queue = [], waiting = true, incoming = "", destroying, maxLength = 0;
    
    function dispatch(){
        if (waiting || queue.length === 0 || destroying) {
            return;
        }
        waiting = true;
        var message = queue.shift();
        
        pub.down.outgoing(message.data, message.origin, function(success){
            waiting = false;
            if (message.callback) {
                setTimeout(function(){
                    message.callback(success);
                }, 0);
            }
            dispatch();
        });
    }
    return (pub = {
        init: function(){
            if (undef(config)) {
                config = {};
            }
            maxLength = config.maxLength ? config.maxLength : 0;
            pub.down.init();
        },
        callback: function(success){
            waiting = false;
            dispatch();
            pub.up.callback(success);
        },
        incoming: function(message, origin){
            var indexOf = message.indexOf("_"), seq = parseInt(message.substring(0, indexOf), 10);
            incoming += message.substring(indexOf + 1);
            if (seq === 0) {
                if (config.encode) {
                    incoming = decodeURIComponent(incoming);
                }
                pub.up.incoming(incoming, origin);
                incoming = "";
            }
        },
        outgoing: function(message, origin, fn){
            if (config.encode) {
                message = encodeURIComponent(message);
            }
            var fragments = [], fragment;
            if (maxLength) {
                while (message.length !== 0) {
                    fragment = message.substring(0, maxLength);
                    message = message.substring(fragment.length);
                    fragments.push(fragment);
                }
            }
            else {
                fragments.push(message);
            }
            while ((fragment = fragments.shift())) {
                queue.push({
                    data: fragments.length + "_" + fragment,
                    origin: origin,
                    callback: fragments.length === 0 ? fn : null
                });
            }
            dispatch();
        },
        destroy: function(){
            destroying = true;
            pub.down.destroy();
        }
    });
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, undef */

/**
 * @class easyXDM.stack.VerifyBehavior
 * This behavior will verify that communication with the remote end is possible, and will also sign all outgoing,
 * and verify all incoming messages. This removes the risk of someone hijacking the iframe to send malicious messages.
 * @namespace easyXDM.stack
 * @constructor
 * @param {Object} config The behaviors configuration.
 * @cfg {Boolean} initiate If the verification should be initiated from this end.
 */
easyXDM.stack.VerifyBehavior = function(config){
    var pub, mySecret, theirSecret, verified = false;
    
    function startVerification(){
        mySecret = Math.random().toString(16).substring(2);
        pub.down.outgoing(mySecret);
    }
    
    return (pub = {
        incoming: function(message, origin){
            var indexOf = message.indexOf("_");
            if (indexOf === -1) {
                if (message === mySecret) {
                    pub.up.callback(true);
                }
                else if (!theirSecret) {
                    theirSecret = message;
                    if (!config.initiate) {
                        startVerification();
                    }
                    pub.down.outgoing(message);
                }
            }
            else {
                if (message.substring(0, indexOf) === theirSecret) {
                    pub.up.incoming(message.substring(indexOf + 1), origin);
                }
            }
        },
        outgoing: function(message, origin, fn){
            pub.down.outgoing(mySecret + "_" + message, origin, fn);
        },
        callback: function(success){
            if (config.initiate) {
                startVerification();
            }
        }
    });
};
/*jslint evil: true, browser: true, immed: true, passfail: true, undef: true, newcap: true*/
/*global easyXDM, window, escape, unescape, undef, getJSON, debug, emptyFn */

/**
 * @class easyXDM.stack.RpcBehavior
 * This uses JSON-RPC 2.0 to expose local methods and to invoke remote methods and have responses returned over the the string based transport stack.<br/>
 * Exposed methods can return values synchronous, asyncronous, or bet set up to not return anything.
 * @namespace easyXDM.stack
 * @constructor
 * @param {Object} proxy The object to apply the methods to.
 * @param {Object} config The definition of the local and remote interface to implement.
 * @cfg {Object} local The local interface to expose.
 * @cfg {Object} remote The remote methods to expose through the proxy.
 * @cfg {Object} serializer The serializer to use for serializing and deserializing the JSON. Should be compatible with the HTML5 JSON object. Optional, will default to JSON.
 */
easyXDM.stack.RpcBehavior = function(proxy, config){
    var pub, serializer = config.serializer || getJSON();
    var _callbackCounter = 0, _callbacks = {};
    
    /**
     * Serializes and sends the message
     * @private
     * @param {Object} data The JSON-RPC message to be sent. The jsonrpc property will be added.
     */
    function _send(data){
        data.jsonrpc = "2.0";
        pub.down.outgoing(serializer.stringify(data));
    }
    
    /**
     * Creates a method that implements the given definition
     * @private
     * @param {Object} The method configuration
     * @param {String} method The name of the method
     * @return {Function} A stub capable of proxying the requested method call
     */
    function _createMethod(definition, method){
        var slice = Array.prototype.slice;
        
        return function(){
            var l = arguments.length, callback, message = {
                method: method
            };
            
            if (l > 0 && typeof arguments[l - 1] === "function") {
                //with callback, procedure
                if (l > 1 && typeof arguments[l - 2] === "function") {
                    // two callbacks, success and error
                    callback = {
                        success: arguments[l - 2],
                        error: arguments[l - 1]
                    };
                    message.params = slice.call(arguments, 0, l - 2);
                }
                else {
                    // single callback, success
                    callback = {
                        success: arguments[l - 1]
                    };
                    message.params = slice.call(arguments, 0, l - 1);
                }
                _callbacks["" + (++_callbackCounter)] = callback;
                message.id = _callbackCounter;
            }
            else {
                // no callbacks, a notification
                message.params = slice.call(arguments, 0);
            }
            // Send the method request
            _send(message);
        };
    }
    
    /**
     * Executes the exposed method
     * @private
     * @param {String} method The name of the method
     * @param {Number} id The callback id to use
     * @param {Function} method The exposed implementation
     * @param {Array} params The parameters supplied by the remote end
     */
    function _executeMethod(method, id, fn, params){
        if (!fn) {
            if (id) {
                _send({
                    id: id,
                    error: {
                        code: -32601,
                        message: "Procedure not found."
                    }
                });
            }
            return;
        }
        
        var used = false, success, error;
        if (id) {
            success = function(result){
                if (used) {
                    return;
                }
                used = true;
                _send({
                    id: id,
                    result: result
                });
            };
            error = function(message){
                if (used) {
                    return;
                }
                used = true;
                _send({
                    id: id,
                    error: {
                        code: -32099,
                        message: "Application error: " + message
                    }
                });
            };
        }
        else {
            success = error = emptyFn;
        }
        // Call local method
        try {
            var result = fn.method.apply(fn.scope, params.concat([success, error]));
            if (!undef(result)) {
                success(result);
            }
        } 
        catch (ex1) {
            error(ex1.message);
        }
    }
    
    return (pub = {
        incoming: function(message, origin){
            var data = serializer.parse(message);
            if (data.method) {
                // A method call from the remote end
                if (config.handle) {
                    config.handle(data, _send);
                }
                else {
                    _executeMethod(data.method, data.id, config.local[data.method], data.params);
                }
            }
            else {
                // A method response from the other end
                var callback = _callbacks[data.id];
                if (data.error) {
                    if (callback.error) {
                        callback.error(data.error);
                    }
                }
                else if (callback.success) {
                    callback.success(data.result);
                }
                delete _callbacks[data.id];
            }
        },
        init: function(){
            if (config.remote) {
                // Implement the remote sides exposed methods
                for (var method in config.remote) {
                    if (config.remote.hasOwnProperty(method)) {
                        proxy[method] = _createMethod(config.remote[method], method);
                    }
                }
            }
            pub.down.init();
        },
        destroy: function(){
            for (var method in config.remote) {
                if (config.remote.hasOwnProperty(method) && proxy.hasOwnProperty(method)) {
                    delete proxy[method];
                }
            }
            pub.down.destroy();
        }
    });
};
})(window, document, location, window.setTimeout, decodeURIComponent, encodeURIComponent);
