"use strict";

(function () {
  var STYLE_ID = "abyss-spotlight-frame-style";
  var FRAME_CLASS = "featurediframe";

  var spotlightUrl = "ui/spotlight.html";
  try {
    var cs = document.currentScript;
    if (cs && cs.src) {
      spotlightUrl = new URL("spotlight.html", cs.src).href;
    }
  } catch (e) {
    // Fall back to the relative default above.
  }

  var lifecycleObserver = null;
  var lifecycleCleanup = function () { };
  var currentIndexPage = null;
  var currentHomeTab = null;
  var currentFavoritesTab = null;
  var currentIframe = null;
  var backdropOverlay = null;
  var backdropLayerA = null;
  var backdropLayerB = null;
  var activeBackdropLayer = null;

  function safe(fn) {
    // Runs fn and swallows/reports any error so one failure never kills the loader.
    try {
      fn();
    } catch (err) {
      try {
        console.warn("[abyss-spotlight]", err);
      } catch (e2) {
        // console unavailable, nothing more we can do
      }
    }
  }

  var BACKDROP_SELECTOR = ".backdropContainer .backdropImage";
  var BACKDROP_MARK_ATTR = "data-abyss-spotlight-backdrop";

  function applySpotlightBackdrop(url) {
    if (!url) { clearSpotlightBackdrop(); return; }
    safe(function () {
      var els = document.querySelectorAll(BACKDROP_SELECTOR);
      for (var i = 0; i < els.length; i++) {
        els[i].setAttribute(BACKDROP_MARK_ATTR, "true");
        els[i].style.backgroundImage = 'url("' + url + '")';
        els[i].style.imageRendering = 'auto';
      }
    });
  }

  function clearSpotlightBackdrop() {
    safe(function () {
      var els = document.querySelectorAll(BACKDROP_SELECTOR + "[" + BACKDROP_MARK_ATTR + "]");
      for (var i = 0; i < els.length; i++) {
        els[i].style.backgroundImage = "";
        els[i].removeAttribute(BACKDROP_MARK_ATTR);
      }
    });
  }

  function clearSpotlightLifecycle() {
    safe(lifecycleCleanup);
    lifecycleCleanup = function () { };
    lifecycleObserver = null;
    currentIndexPage = null;
    currentHomeTab = null;
    currentFavoritesTab = null;
    currentIframe = null;
    currentSync = null;
    spotlightFocused = false;
    document.documentElement.classList.remove("abyss-spotlight-visible");
    clearSpotlightBackdrop();
  }

  function installFrameStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent =
      "#indexPage.abyss-spotlight-active { padding: 0 !important; }" +
      "#homeTab.abyss-spotlight-active { padding: 0 !important; margin: 0 !important; }" +
      "." + FRAME_CLASS + " { width:100%;display:block;border:0;margin:0;padding:0;height:58vh;min-height:420px;max-height:640px; }" +
      "." + FRAME_CLASS + ":focus { outline: none; }" +
      "@media (min-width:1400px) { ." + FRAME_CLASS + " { height:60vh;max-height:720px; } }" +
      "@media (min-width:1920px) { ." + FRAME_CLASS + " { height:56vh;max-height:800px; } }" +
      "@media (max-width:1024px) and (orientation:portrait) { ." + FRAME_CLASS + " { height:50vh;min-height:360px;max-height:480px; } }" +
      "@media (max-width:768px) and (orientation:portrait) { ." + FRAME_CLASS + " { height:46vh;min-height:330px;max-height:430px; } }" +
      "@media (orientation:landscape) and (max-height:540px) { ." + FRAME_CLASS + " { height:86vh;min-height:300px;max-height:460px; } }";
    document.head.appendChild(style);
  }

  function installBackdropOverlay() {
    if (backdropOverlay) return;
    var container = document.querySelector(".backdropContainer");
    if (!container || !container.parentNode) return;

    backdropOverlay = document.createElement("div");
    backdropOverlay.id = "abyss-spotlight-backdrop";
    backdropLayerA = document.createElement("div");
    backdropLayerB = document.createElement("div");
    backdropLayerA.className = "abyss-spotlight-backdrop-layer";
    backdropLayerB.className = "abyss-spotlight-backdrop-layer";
    backdropOverlay.appendChild(backdropLayerA);
    backdropOverlay.appendChild(backdropLayerB);

    container.parentNode.insertBefore(backdropOverlay, container.nextSibling);

    var style = document.createElement("style");
    style.id = "abyss-spotlight-backdrop-style";
    style.textContent =
      "#abyss-spotlight-backdrop{position:fixed;inset:0;pointer-events:none;opacity:0;transition:opacity .6s ease;}" +
      "html.abyss-spotlight-visible #abyss-spotlight-backdrop{opacity:1;}" +
      ".abyss-spotlight-backdrop-layer{position:absolute;inset:0;background-size:cover;background-position:center;opacity:0;" +
      "transition:opacity .9s ease;filter:blur(var(--abyss-backdrop-blur,23px)) saturate(120%) contrast(120%) brightness(25%);}" +
      ".abyss-spotlight-backdrop-layer.is-active{opacity:1;}";
    document.head.appendChild(style);
  }

  function setSpotlightBackdrop(url) {
    if (!url || !backdropOverlay) return;
    safe(function () {
      var incoming = activeBackdropLayer === backdropLayerA ? backdropLayerB : backdropLayerA;
      var outgoing = activeBackdropLayer;

      var img = new Image();
      img.onload = function () {
        safe(function () {
          incoming.style.backgroundImage = 'url("' + url + '")';
          requestAnimationFrame(function () {
            incoming.classList.add("is-active");
            if (outgoing && outgoing !== incoming) {
              setTimeout(function () {
                outgoing.classList.remove("is-active");
              }, 50);
            }
          });
          activeBackdropLayer = incoming;
        });
      };
      img.src = url;
    });
  }

  function postToFrame(iframe, action) {
    if (!iframe || !iframe.contentWindow) return;
    var targetOrigin = "*";
    try {
      if (window.location && window.location.origin && window.location.origin !== "null") {
        targetOrigin = window.location.origin;
      }
    } catch (e) {
      // keep "*" fallback
    }
    safe(function () {
      iframe.contentWindow.postMessage({ type: "abyss-spotlight", action: action }, targetOrigin);
    });
  }


  var spotlightFocused = false;

  function isEditableElement(el) {
    var tag = el && el.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || (el && el.isContentEditable);
  }

  function nearestFocusable(originRect, direction, pool) {
    var originX = originRect.left + originRect.width / 2;
    var originY = direction === "up" ? originRect.top : originRect.bottom;

    var candidates = pool.filter(function (el) {
      if (!el.isConnected) return false;
      var r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return false;
      return direction === "down" ? r.top >= originRect.bottom - 4 : r.bottom <= originRect.top + 4;
    });

    if (!candidates.length) return null;

    candidates.sort(function (a, b) {
      var ra = a.getBoundingClientRect();
      var rb = b.getBoundingClientRect();
      var da = Math.hypot(ra.left + ra.width / 2 - originX, ra.top - originY);
      var db = Math.hypot(rb.left + rb.width / 2 - originX, rb.top - originY);
      return da - db;
    });

    return candidates[0];
  }

  function enterSpotlight(iframe) {
    spotlightFocused = true;
    safe(function () { iframe.focus(); });
    postToFrame(iframe, "tv-focus");
  }

  document.addEventListener("keydown", function (event) {
    if (spotlightFocused) return; // events go straight to the iframe's own document while it holds focus
    if (!currentIframe || !currentIframe.isConnected) return;
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;

    var active = document.activeElement;
    if (!active || active === document.body || isEditableElement(active)) return;

    var direction = event.key === "ArrowDown" ? "down" : "up";
    var pool = Array.prototype.slice.call(document.querySelectorAll(".focusable")).concat([currentIframe]);
    var nearest = nearestFocusable(active.getBoundingClientRect(), direction, pool);

    if (nearest === currentIframe) {
      event.preventDefault();
      event.stopPropagation();
      enterSpotlight(currentIframe);
    }
  }, true); // capture phase... runs before Jellyfin's own keydown handling

  function focusNearestOutside(iframe, direction) {
    try {
      var rect = iframe.getBoundingClientRect();
      var pool = Array.prototype.slice
        .call(document.querySelectorAll(".focusable, .itemsContainer .card, .headerButton, .paper-icon-button-light"))
        .filter(function (el) { return el !== iframe && el.offsetParent !== null; });
      var nearest = nearestFocusable(rect, direction, pool);
      if (!nearest) {
        if (direction === "down") {
          nearest = document.querySelector(".itemsContainer .card");
        } else {
          nearest = document.querySelector(".headerButton, .headerLeft button");
        }
      }
      if (!nearest) return false;
      nearest.focus();
      if (nearest.scrollIntoView) {
        nearest.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  window.addEventListener("message", function (event) {
    if (!currentIframe || event.source !== currentIframe.contentWindow) return;
    if (!event.data || event.data.type !== "abyss-spotlight") return;
    if (event.data.action === "leave") {
      spotlightFocused = false;
      safe(function () {
        focusNearestOutside(currentIframe, event.data.direction || "down");
      });
      return;
    }
    if (event.data.action === "backdrop-sync") {
      if (document.documentElement.classList.contains("abyss-spotlight-visible")) {
        setSpotlightBackdrop(event.data.url);
      }
      return;
    }
  });

  function isRouteVisible(indexPage, homeTab) {
    if (!indexPage || !indexPage.isConnected || !homeTab || !homeTab.isConnected) return false;
    if (document.hidden) return false;
    if (indexPage.classList.contains("hide") || indexPage.hidden) return false;
    var style = window.getComputedStyle(homeTab);
    if (style.display === "none") return false;
    return homeTab.offsetParent !== null || homeTab.getClientRects().length > 0 || !homeTab.classList.contains("hide");
  }

  function connectLifecycle(indexPage, homeTab, favoritesTab, iframe) {
    safe(lifecycleCleanup);
    var lastAction = "";

    var sync = function () {
      safe(function () {
        if (!iframe || !iframe.isConnected) {
          clearSpotlightLifecycle();
          return;
        }
        var favoritesActive = !!(favoritesTab && favoritesTab.classList && favoritesTab.classList.contains("is-active"));
        var active = isRouteVisible(indexPage, homeTab) && !favoritesActive;
        var action = active ? "resume" : "pause";
        document.documentElement.classList.toggle("abyss-spotlight-visible", active);
        iframe.style.display = active ? "block" : "none";
        if (action !== lastAction) {
          postToFrame(iframe, action);
          lastAction = action;
          if (action === "pause") clearSpotlightBackdrop();
        }
      });
    };

    if (typeof MutationObserver === "function") {
      safe(function () {
        lifecycleObserver = new MutationObserver(sync);
        lifecycleObserver.observe(indexPage, { attributes: true, attributeFilter: ["class", "hidden"] });
        lifecycleObserver.observe(homeTab, { attributes: true, attributeFilter: ["class", "style"] });
        if (favoritesTab) lifecycleObserver.observe(favoritesTab, { attributes: true, attributeFilter: ["class"] });
        var ancestor = indexPage.parentElement;
        while (ancestor) {
          lifecycleObserver.observe(ancestor, { attributes: true, attributeFilter: ["class", "hidden", "style"] });
          if (ancestor === document.body) break;
          ancestor = ancestor.parentElement;
        }
      });
    }

    var handleLoad = function () {
      lastAction = "";
      sync();
    };
    iframe.addEventListener("load", handleLoad);
    document.addEventListener("visibilitychange", sync);

    lifecycleCleanup = function () {
      if (lifecycleObserver) safe(function () { lifecycleObserver.disconnect(); });
      iframe.removeEventListener("load", handleLoad);
      document.removeEventListener("visibilitychange", sync);
    };

    sync();

    return sync;
  }

  var currentSync = null;

  function findVisibleById(id) {
    var candidates = document.querySelectorAll('[id="' + id + '"]');
    for (var i = 0; i < candidates.length; i++) {
      var el = candidates[i];
      if (
        el.isConnected &&
        !el.classList.contains("hide") &&
        !el.hidden
      ) {
        return el;
      }
    }
    return candidates.length ? candidates[candidates.length - 1] : null;
  }

  function installSpotlight() {
    var installed = false;
    safe(function () {
      var indexPage = findVisibleById("indexPage");
      if (!indexPage) {
        clearSpotlightLifecycle();
        return;
      }
      var homeTab = indexPage.querySelector("#homeTab");
      if (!homeTab) {
        clearSpotlightLifecycle();
        return;
      }
      var favoritesTab = indexPage.querySelector("#favoritesTab");

      installFrameStyle();
      installBackdropOverlay();

      var iframe = homeTab.querySelector ? homeTab.querySelector("." + FRAME_CLASS) : null;
      if (!iframe) {
        iframe = document.createElement("iframe");
        iframe.className = FRAME_CLASS + " focusable";
        iframe.setAttribute("tabindex", "0");
        iframe.src = spotlightUrl;
        iframe.title = "Abyss Spotlight";
        iframe.addEventListener("blur", function () { spotlightFocused = false; });
        var sections = homeTab.querySelector ? homeTab.querySelector(".sections") : null;
        homeTab.insertBefore(iframe, sections || homeTab.firstChild);
      }

      safe(function () {
        if (indexPage.classList) indexPage.classList.add("abyss-spotlight-active");
        if (homeTab.classList) homeTab.classList.add("abyss-spotlight-active");
      });

      if (
        indexPage !== currentIndexPage ||
        homeTab !== currentHomeTab ||
        favoritesTab !== currentFavoritesTab ||
        iframe !== currentIframe
      ) {
        currentIndexPage = indexPage;
        currentHomeTab = homeTab;
        currentFavoritesTab = favoritesTab;
        currentIframe = iframe;
        currentSync = connectLifecycle(indexPage, homeTab, favoritesTab, iframe);
      }
      installed = true;
    });
    return installed;
  }

  function removeAlphaPicker() {
    safe(function () {
      var pickers = document.querySelectorAll(
        ".alphaPicker, .alphaPicker-fixed, .alphaPicker-fixed-right, .alphanumeric-scrollbar, div[class*='alphaPicker'], div[class*='alphanumeric'], div[class*='alpha-picker'], #alpha-scrubber-hud"
      );
      for (var i = 0; i < pickers.length; i++) {
        var el = pickers[i];
        if (el && el.parentNode) {
          el.parentNode.removeChild(el);
        }
      }
    });
  }

  function installClaudeMenuIcon() {
    safe(function () {
      var svgs = document.querySelectorAll(
        'svg[data-testid="MenuIcon"], button[aria-label="Menu"] svg, button[aria-label="menu"] svg, .mainDrawerButton svg'
      );
      for (var i = 0; i < svgs.length; i++) {
        var svg = svgs[i];
        if (svg.getAttribute("data-claude-menu") === "true") continue;
        svg.setAttribute("data-claude-menu", "true");
        svg.classList.add("claude-stepped-menu");
        svg.setAttribute("viewBox", "0 0 20 15");
        svg.setAttribute("width", "20");
        svg.setAttribute("height", "15");
        svg.style.width = "20px";
        svg.style.height = "15px";
        svg.innerHTML =
          '<rect x="0" y="0.5" width="20" height="2" rx="1" fill="white"/>' +
          '<rect x="0" y="6.5" width="13.5" height="2" rx="1" fill="white"/>' +
          '<rect x="0" y="12.5" width="7.5" height="2" rx="1" fill="white"/>';
      }

      var classicBtns = document.querySelectorAll(
        ".mainDrawerButton:not(:has(svg)), .headerButtonMenu:not(:has(svg))"
      );
      for (var j = 0; j < classicBtns.length; j++) {
        var btn = classicBtns[j];
        if (btn.getAttribute("data-claude-menu") === "true") continue;
        btn.setAttribute("data-claude-menu", "true");
        btn.innerHTML =
          '<svg class="claude-stepped-menu" viewBox="0 0 20 15" width="20" height="15">' +
          '<rect x="0" y="0.5" width="20" height="2" rx="1" fill="white"/>' +
          '<rect x="0" y="6.5" width="13.5" height="2" rx="1" fill="white"/>' +
          '<rect x="0" y="12.5" width="7.5" height="2" rx="1" fill="white"/>' +
          '</svg>';
      }
    });
  }

  var APEX_DELTA_SVG =
    '<svg class="apex-delta-icon" viewBox="215 376 1460 1460" width="22" height="22" style="display:inline-block;vertical-align:middle;max-width:24px;max-height:24px;object-fit:contain;" aria-label="Apex">' +
    '<polygon points="839,417 990,417 990,683 839,683" fill="white"/>' +
    '<polygon points="511,1000 662,1000 662,1266 511,1266" fill="white"/>' +
    '<polygon points="990,1479 990,1746 839,1746 839,1479" fill="white"/>' +
    '<polygon points="1318,1000 1469,1000 1469,1266 1318,1266" fill="white"/>' +
    '<polygon points="794,443 1035,443 1494,975 1494,1291 1035,1720 794,1720 1253,1291 1253,975" fill="white"/>' +
    '<polygon points="486,975 727,443 968,443 727,975" fill="white"/>' +
    '<polygon points="486,1291 727,1720 968,1720 727,1291" fill="white"/>' +
    '</svg>';

  function installApexBranding() {
    safe(function () {
      var logoSvgUrl = (window.location.pathname.indexOf("/web") !== -1) ? "ui/apex-logo.svg" : "/jellyfin/web/ui/apex-logo.svg";

      // 1. Favicon sync
      var links = document.querySelectorAll("link[rel*='icon']");
      for (var i = 0; i < links.length; i++) {
        if (links[i].getAttribute("data-apex-logo") !== "true") {
          links[i].setAttribute("data-apex-logo", "true");
          links[i].href = logoSvgUrl;
        }
      }
      if (links.length === 0 && document.head) {
        var link = document.createElement("link");
        link.rel = "icon";
        link.type = "image/svg+xml";
        link.href = logoSvgUrl;
        link.setAttribute("data-apex-logo", "true");
        document.head.appendChild(link);
      }

      // 2. Target ONLY explicit app brand logos (NEVER media cards, posters, or user avatars!)
      var targetImgs = document.querySelectorAll(
        '.headerLogo img, .adminDrawerLogo img, .mainDrawer a[to="/"] img, .mainDrawer a[href="/"] img, img.imgLogoIcon, img.headerLogo'
      );
      for (var k = 0; k < targetImgs.length; k++) {
        var imgEl = targetImgs[k];
        // Hard safeguard: never touch cards, backdrops, or user avatars
        if (imgEl.closest('.card, .cardBox, .cardScalable, .detailImage, .headerButton-user, .userImage')) continue;
        if (imgEl.src && !imgEl.src.includes("apex-logo")) {
          imgEl.src = logoSvgUrl;
          imgEl.srcset = "";
        }
      }

      // 3. Header & Drawer logo elements (without destroying drawer labels)
      var headerLogos = document.querySelectorAll(".headerLogo, .pageTitleWithDefaultLogo");
      for (var h = 0; h < headerLogos.length; h++) {
        var hl = headerLogos[h];
        if (hl.querySelector("img") || hl.querySelector(".apex-delta-icon")) continue;
        hl.innerHTML = APEX_DELTA_SVG;
      }

      // 4. Drawer logo (compact 22px as requested, perfectly aligned with text)
      var drawerLinks = document.querySelectorAll(".mainDrawer a[to='/'], .mainDrawer a[href='/'], .mainDrawer .adminDrawerLogo");
      for (var d = 0; d < drawerLinks.length; d++) {
        var dEl = drawerLinks[d];
        if (!dEl.querySelector(".apex-delta-icon") && !dEl.querySelector("img[src*='apex-logo']")) {
          var existingImg = dEl.querySelector("img");
          if (existingImg) {
            existingImg.src = logoSvgUrl;
            existingImg.style.width = "22px";
            existingImg.style.height = "22px";
          } else {
            var iconSpan = document.createElement("span");
            iconSpan.className = "apex-drawer-logo-container";
            iconSpan.style.cssText = "display:inline-flex;align-items:center;justify-content:center;margin-right:10px;vertical-align:middle;";
            iconSpan.innerHTML = APEX_DELTA_SVG;
            dEl.insertBefore(iconSpan, dEl.firstChild);
          }
        }
      }
    });
  }

  function applyBrandedLibraryFallback(container, title) {
    if (!container) return;
    container.style.background = "linear-gradient(135deg, #1a1a26 0%, #0d0d14 50%, #050508 100%)";
  }

  function enhanceLibraryCards() {
    safe(function () {
      var libraryCards = document.querySelectorAll(
        '.card[data-type="CollectionFolder"], [data-category="views"] .card, .homeSectionsContainer .verticalSection:first-of-type .card'
      );
      if (!libraryCards || !libraryCards.length) return;

      var baseUrl = "";
      try {
        baseUrl = (window.ApiClient && typeof window.ApiClient.serverAddress === "function" && window.ApiClient.serverAddress()) || window.location.origin;
      } catch (e) {
        baseUrl = window.location.origin;
      }

      var token = "";
      var userId = "";
      try {
        if (window.ApiClient) {
          token = (typeof window.ApiClient.accessToken === "function") ? window.ApiClient.accessToken() : "";
          userId = (typeof window.ApiClient.getCurrentUserId === "function") ? window.ApiClient.getCurrentUserId() : "";
        }
      } catch (e) {}

      for (var i = 0; i < libraryCards.length; i++) {
        (function (card) {
          if (!card.hasAttribute("tabindex")) card.setAttribute("tabindex", "0");
          card.classList.add("apex-library-card");

          var imgContainer = card.querySelector(".cardImageContainer") || card.querySelector(".cardScalable");
          if (!imgContainer) return;

          if (card.getAttribute("data-apex-bg-applied") === "true") return;

          var itemId = card.getAttribute("data-id") || (card.dataset && card.dataset.id);
          var cardName = card.querySelector(".cardText, .cardText-first, .cardLargeText");
          var libraryTitle = cardName ? cardName.textContent.trim() : "Library";

          if (itemId && userId && token && baseUrl) {
            var queryUrl = baseUrl + "/Users/" + userId + "/Items?ParentId=" + itemId +
              "&Limit=1&Recursive=true&SortBy=DateCreated&SortOrder=Descending&IncludeItemTypes=Movie,Series,Episode&Fields=BackdropImageTags,ParentBackdropImageTags&ImageTypes=Backdrop";

            fetch(queryUrl, {
              headers: {
                "Authorization": 'MediaBrowser Client="Jellyfin Web", Device="Apex UI", DeviceId="apex-web", Version="1.0", Token="' + token + '"'
              }
            })
              .then(function (res) { return res.ok ? res.json() : null; })
              .then(function (data) {
                if (data && data.Items && data.Items.length > 0) {
                  var item = data.Items[0];
                  var tag = (item.BackdropImageTags && item.BackdropImageTags[0]) ||
                            (item.ParentBackdropImageTags && item.ParentBackdropImageTags[0]);
                  var bId = item.Id;
                  if (tag) {
                    var imgUrl = baseUrl + "/Items/" + bId + "/Images/Backdrop/0?maxWidth=1280&quality=90&tag=" + tag;
                    imgContainer.style.backgroundImage = 'url("' + imgUrl + '")';
                    imgContainer.style.backgroundSize = "cover";
                    imgContainer.style.backgroundPosition = "center center";
                    imgContainer.style.backgroundRepeat = "no-repeat";
                    card.setAttribute("data-apex-bg-applied", "true");
                    return;
                  }
                }
                applyBrandedLibraryFallback(imgContainer, libraryTitle);
                card.setAttribute("data-apex-bg-applied", "true");
              })
              .catch(function () {
                applyBrandedLibraryFallback(imgContainer, libraryTitle);
                card.setAttribute("data-apex-bg-applied", "true");
              });
          } else {
            applyBrandedLibraryFallback(imgContainer, libraryTitle);
            card.setAttribute("data-apex-bg-applied", "true");
          }
        })(libraryCards[i]);
      }
    });
  }

    function installTopNavigation() {
    safe(function () {
      var header = document.querySelector(".skinHeader, .skinHeader-withBackground, header");
      if (!header) return;
      if (header.querySelector(".apex-top-nav") || document.querySelector(".apex-top-nav")) return;

      var navContainer = document.createElement("div");
      navContainer.className = "apex-top-nav";
      var categories = [
        { label: "Home", hash: "#/home" },
        { label: "Movies", hash: "#/movies" },
        { label: "Series", hash: "#/shows" },
        { label: "My Library", hash: "#/library" }
      ];

      var currentHash = window.location.hash || "";

      function updateActiveTab() {
        var hash = window.location.hash || "";
        var links = navContainer.querySelectorAll(".apex-nav-item");
        for (var i = 0; i < links.length; i++) {
          var item = links[i];
          var navType = item.getAttribute("data-nav");
          var isActive = false;
          if (navType === "Home" && (!hash || hash.indexOf("/home") !== -1 || hash === "#/" || hash === "#")) {
            isActive = true;
          } else if (navType === "Movies" && (hash.indexOf("movie") !== -1 || hash.indexOf("Movie") !== -1)) {
            isActive = true;
          } else if (navType === "Series" && (hash.indexOf("show") !== -1 || hash.indexOf("series") !== -1 || hash.indexOf("tv") !== -1)) {
            isActive = true;
          } else if (navType === "My Library" && hash.indexOf("library") !== -1) {
            isActive = true;
          }
          if (isActive) item.classList.add("active");
          else item.classList.remove("active");
        }
      }

      categories.forEach(function (cat) {
        var a = document.createElement("a");
        var isHome = cat.label === "Home" && (!currentHash || currentHash.indexOf("/home") !== -1 || currentHash === "#/" || currentHash === "#");
        a.className = "apex-nav-item" + (isHome ? " active" : "");
        a.textContent = cat.label;
        a.href = cat.hash;
        a.setAttribute("data-nav", cat.label);
        a.addEventListener("click", function (e) {
          e.preventDefault();
          var allLinks = document.querySelectorAll(".apex-nav-item");
          for (var i = 0; i < allLinks.length; i++) allLinks[i].classList.remove("active");
          a.classList.add("active");

          if (cat.label === "Home") {
            window.location.hash = "#/home";
            window.scrollTo({ top: 0, behavior: "smooth" });
          } else if (cat.label === "Movies") {
            var targetMovie = document.querySelector('.card[data-type="Movie"], .card[data-name*="Movie" i], .lnkMediaFolder[title*="Movie" i], .navMenuOption[title*="Movie" i]');
            if (targetMovie && targetMovie.click) {
              targetMovie.click();
            } else {
              window.location.hash = "#/movies";
            }
          } else if (cat.label === "Series") {
            var targetSeries = document.querySelector('.card[data-type="Series"], .card[data-name*="Series" i], .card[data-name*="Show" i], .lnkMediaFolder[title*="Series" i], .lnkMediaFolder[title*="Show" i], .navMenuOption[title*="Series" i], .navMenuOption[title*="Show" i]');
            if (targetSeries && targetSeries.click) {
              targetSeries.click();
            } else {
              window.location.hash = "#/shows";
            }
          } else {
            var targetLib = document.querySelector('.lnkMediaFolder[title*="Library" i], .navMenuOption[title*="Library" i]');
            if (targetLib && targetLib.click) {
              targetLib.click();
            } else {
              window.location.hash = cat.hash;
            }
          }
        });
        navContainer.appendChild(a);
      });

      window.addEventListener("hashchange", updateActiveTab);
      updateActiveTab();

      var headerTop = header.querySelector(".headerTop") || header;
      var headerLeft = headerTop.querySelector(".headerLeft") || headerTop.querySelector(".mainDrawerButton") || headerTop.firstChild;
      if (headerLeft && headerLeft.parentNode) {
        headerLeft.parentNode.insertBefore(navContainer, headerLeft.nextSibling);
      } else {
        headerTop.insertBefore(navContainer, headerTop.firstChild);
      }
    });
  }

  var dpadInstalled = false;
  function installSpatialDpadNavigation() {
    safe(function () {
      function ensureCardFocusable() {
        var cards = document.querySelectorAll(".itemsContainer .card:not([tabindex])");
        for (var i = 0; i < cards.length; i++) {
          cards[i].setAttribute("tabindex", "0");
        }
      }
      ensureCardFocusable();

      if (dpadInstalled) return;
      dpadInstalled = true;

      document.addEventListener("keydown", function (e) {
        if (spotlightFocused) return;
        var key = e.key;
        if (key !== "ArrowUp" && key !== "ArrowDown" && key !== "ArrowLeft" && key !== "ArrowRight" && key !== "Enter") {
          return;
        }

        var active = document.activeElement;
        if (isEditableElement(active)) return;

        ensureCardFocusable();

        var currentCard = active ? active.closest(".card") : null;

        if (!currentCard) {
          if (key === "ArrowDown" && (!active || active === document.body)) {
            var firstCard = document.querySelector(".itemsContainer .card");
            if (firstCard) {
              e.preventDefault();
              firstCard.focus();
              if (firstCard.scrollIntoView) {
                firstCard.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
              }
            }
          }
          return;
        }

        // We are on a card!
        if (key === "Enter") {
          e.preventDefault();
          var clickTarget = currentCard.querySelector("a, button, [data-action]") || currentCard;
          clickTarget.click();
          return;
        }

        if (key === "ArrowLeft" || key === "ArrowRight") {
          e.preventDefault();
          var sibling = key === "ArrowRight" ? currentCard.nextElementSibling : currentCard.previousElementSibling;
          while (sibling && !sibling.classList.contains("card")) {
            sibling = key === "ArrowRight" ? sibling.nextElementSibling : sibling.previousElementSibling;
          }
          if (sibling) {
            sibling.focus();
            if (sibling.scrollIntoView) {
              sibling.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
            }
          }
          return;
        }

        if (key === "ArrowUp" || key === "ArrowDown") {
          e.preventDefault();
          var currentContainer = currentCard.closest(".itemsContainer") || currentCard.parentElement;
          var allContainers = Array.prototype.slice.call(document.querySelectorAll(".itemsContainer"));
          var currentIndex = allContainers.indexOf(currentContainer);

          if (key === "ArrowDown") {
            if (currentIndex !== -1 && currentIndex < allContainers.length - 1) {
              var nextContainer = allContainers[currentIndex + 1];
              var nextCards = nextContainer.querySelectorAll(".card");
              if (nextCards.length > 0) {
                var targetCard = nextCards[0];
                var currentRect = currentCard.getBoundingClientRect();
                var bestDiff = Infinity;
                for (var i = 0; i < nextCards.length; i++) {
                  var r = nextCards[i].getBoundingClientRect();
                  var diff = Math.abs(r.left - currentRect.left);
                  if (diff < bestDiff) {
                    bestDiff = diff;
                    targetCard = nextCards[i];
                  }
                }
                targetCard.focus();
                if (targetCard.scrollIntoView) {
                  targetCard.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
                }
              }
            }
          } else if (key === "ArrowUp") {
            if (currentIndex > 0) {
              var prevContainer = allContainers[currentIndex - 1];
              var prevCards = prevContainer.querySelectorAll(".card");
              if (prevCards.length > 0) {
                var targetCard = prevCards[0];
                var currentRect = currentCard.getBoundingClientRect();
                var bestDiff = Infinity;
                for (var j = 0; j < prevCards.length; j++) {
                  var r = prevCards[j].getBoundingClientRect();
                  var diff = Math.abs(r.left - currentRect.left);
                  if (diff < bestDiff) {
                    bestDiff = diff;
                    targetCard = prevCards[j];
                  }
                }
                targetCard.focus();
                if (targetCard.scrollIntoView) {
                  targetCard.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
                }
              }
            } else {
              // Reached top row - jump into Hero Spotlight or scroll up
              if (currentIframe && currentIframe.isConnected) {
                enterSpotlight(currentIframe);
              } else {
                window.scrollTo({ top: 0, behavior: "smooth" });
              }
            }
          }
        }
      }, true);
    });
  }

  function boot() {
    function ensureDarkTheme() {
      try {
        if (document.documentElement && document.documentElement.getAttribute("data-theme") !== "dark") {
          document.documentElement.setAttribute("data-theme", "dark");
        }
      } catch (e) {}
    }

    function replaceServerNameText() {
      try {
        if (!document.body) return;
        var urlPattern = /r-jishnupg-[a-z0-9-]+|(?:https?:\/\/)?[\w.-]+\.hf\.space[^\s]*|https?:\/\/[^\s<>'"]+|127\.0\.0\.1|localhost:\d+/gi;
        var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
        var node;
        while ((node = walker.nextNode())) {
          if (node.nodeValue && urlPattern.test(node.nodeValue)) {
            node.nodeValue = node.nodeValue.replace(urlPattern, "Apex");
          }
        }
        var targets = document.querySelectorAll(
          ".pageTitle, .sectionTitle, .sectionName, .navMenuOptionText, .headerButton, .sidebarHeader, .cardText, .cardLargeText, .adminDrawerLogo, .btnSelectServer, a[href='/'], a[to='/'], .MuiButton-root, .MuiTypography-root, .MuiListItemText-primary, .MuiListItemText-secondary, .MuiTypography-h6"
        );
        for (var i = 0; i < targets.length; i++) {
          var t = targets[i];
          if (t.textContent && urlPattern.test(t.textContent)) {
            t.textContent = t.textContent.replace(urlPattern, "Apex");
          }
        }
        var hiddenUrls = document.querySelectorAll(".serverUrl, .serverAddress, .manualServerAddress, [class*='serverUrl'], [class*='serverAddress']");
        for (var h = 0; h < hiddenUrls.length; h++) {
          hiddenUrls[h].style.display = "none";
        }
        if (document.title && urlPattern.test(document.title)) {
          document.title = document.title.replace(urlPattern, "Apex");
        }
      } catch (e) {}
    }

    function isSettingsRoute() {
      var hash = (window.location.hash || "").toLowerCase();
      if (
        hash === "" ||
        hash === "#/" ||
        hash.startsWith("#/home") ||
        hash.startsWith("#/movies") ||
        hash.startsWith("#/tv") ||
        hash.startsWith("#/music") ||
        hash.startsWith("#/item") ||
        hash.startsWith("#/details") ||
        hash.startsWith("#/search") ||
        hash.startsWith("#/video") ||
        hash.startsWith("#/favorites")
      ) {
        return false;
      }
      return (
        hash.includes("dashboard") ||
        hash.includes("settings") ||
        hash.includes("preference") ||
        hash.includes("configuration") ||
        hash.includes("wizard") ||
        hash.includes("userprofile") ||
        hash.includes("useredit") ||
        hash.includes("devices") ||
        hash.includes("apikeys") ||
        hash.includes("notifications") ||
        hash.includes("activity") ||
        hash.includes("logs") ||
        Boolean(document.querySelector("#dashboardPage, .pageWithSidebar, .adminDrawerLogo, .dashboardSection"))
      );
    }

    function syncSettingsTheme() {
      var isSettings = isSettingsRoute();
      var themeLink = document.querySelector('link[data-abyss-theme]');
      if (themeLink && themeLink.disabled) {
        themeLink.disabled = false;
      }
      var customCss = document.getElementById("customCss");
      if (customCss && customCss.disabled) {
        customCss.disabled = false;
      }
      if (isSettings) {
        document.documentElement.classList.add("jellyfin-settings-page");
        document.documentElement.classList.remove("abyss-spotlight-active");
        clearSpotlightBackdrop();
        if (currentIframe) {
          currentIframe.style.display = "none";
        }
      } else {
        document.documentElement.classList.remove("jellyfin-settings-page");
        document.documentElement.classList.add("abyss-theme-active");
      }
      ensureDarkTheme();
      replaceServerNameText();
    }

    var installScheduled = false;

    var scheduleInstall = function () {
      syncSettingsTheme();
      if (isSettingsRoute()) {
        return;
      }
      var alreadyGood =
        currentIndexPage && currentIndexPage.isConnected &&
        currentIndexPage === findVisibleById("indexPage") &&
        currentHomeTab && currentHomeTab.isConnected &&
        currentIframe && currentIframe.isConnected &&
        (!currentFavoritesTab || currentFavoritesTab.isConnected);
      if (alreadyGood) return;
      if (installScheduled) return;
      installScheduled = true;

      var run = function () {
        installScheduled = false;
        installSpotlight();
        removeAlphaPicker();
        installClaudeMenuIcon();
        installApexBranding();
      installTopNavigation();
        replaceServerNameText();
        installSpatialDpadNavigation();
        enhanceLibraryCards();
      };

      if (typeof requestAnimationFrame === "function") {
        requestAnimationFrame(run);
      } else {
        setTimeout(run, 16);
      }
    };

    syncSettingsTheme();
    ensureDarkTheme();
    installApexBranding();
      installTopNavigation();
    replaceServerNameText();
    installSpatialDpadNavigation();
    enhanceLibraryCards();
    window.addEventListener("hashchange", syncSettingsTheme);
    if (typeof MutationObserver === "function") {
      safe(function () {
        if (document.documentElement) {
          var themeObserver = new MutationObserver(function () {
            syncSettingsTheme();
            if (!isSettingsRoute()) ensureDarkTheme();
          });
          themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
        }
        if (document.body) {
          var observer = new MutationObserver(function () {
            scheduleInstall();
          });
          observer.observe(document.body, { childList: true, subtree: true });
        }
      });
    }

    // Safety-net poll: re-verifies element connectivity and forces a fresh
    // visibility sync every 2s, so stale SPA navigation state self-corrects
    // without needing a hard refresh.
    setInterval(function () {
      syncSettingsTheme();
      scheduleInstall();
      removeAlphaPicker();
      installClaudeMenuIcon();
      installApexBranding();
      installTopNavigation();
      replaceServerNameText();
      installSpatialDpadNavigation();
      enhanceLibraryCards();
      if (currentSync) safe(currentSync);
    }, 2000);

    installSpotlight();
  }

  function start() {
    safe(function () {
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot, { once: true });
      } else {
        boot();
      }
    });
  }

  start();
})();