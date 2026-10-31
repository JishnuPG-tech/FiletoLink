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
  var currentBackdropUrl = null;

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
      currentBackdropUrl = null;
      if (backdropLayerA) {
        backdropLayerA.classList.remove("is-active");
        backdropLayerA.style.backgroundImage = "";
      }
      if (backdropLayerB) {
        backdropLayerB.classList.remove("is-active");
        backdropLayerB.style.backgroundImage = "";
      }
      activeBackdropLayer = null;
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
      "@media (max-width:1024px) and (orientation:portrait) { ." + FRAME_CLASS + " { height:64vh;min-height:480px;max-height:640px; } }" +
      "@media (max-width:768px) and (orientation:portrait) { ." + FRAME_CLASS + " { height:68vh;min-height:500px;max-height:640px; } }" +
      "@media (orientation:landscape) and (max-height:540px) { ." + FRAME_CLASS + " { height:86vh;min-height:300px;max-height:460px; } }";
    document.head.appendChild(style);
  }

  function installBackdropOverlay() {
    if (backdropOverlay && backdropOverlay.isConnected) return;
    var container = document.querySelector(".backgroundContainer") || document.querySelector(".backdropContainer") || document.body;
    if (!container) return;

    if (!backdropOverlay) {
      backdropOverlay = document.createElement("div");
      backdropOverlay.id = "abyss-spotlight-backdrop";
      backdropLayerA = document.createElement("div");
      backdropLayerB = document.createElement("div");
      backdropLayerA.className = "abyss-spotlight-backdrop-layer";
      backdropLayerB.className = "abyss-spotlight-backdrop-layer";
      backdropOverlay.appendChild(backdropLayerA);
      backdropOverlay.appendChild(backdropLayerB);
    }

    if (!backdropOverlay.isConnected) {
      if (container === document.body) {
        document.body.insertBefore(backdropOverlay, document.body.firstChild);
      } else if (container.parentNode) {
        container.parentNode.insertBefore(backdropOverlay, container.nextSibling);
      } else {
        document.body.appendChild(backdropOverlay);
      }
    }
  }

  function setSpotlightBackdrop(url) {
    if (!url) return;
    currentBackdropUrl = url;
    installBackdropOverlay();
    if (!backdropOverlay) return;
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
              }, 450);
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
    if (!homeTab || !homeTab.isConnected) return false;
    if (document.hidden) return false;
    var hash = window.location.hash || "";
    if (hash && hash !== "#/" && hash !== "#" && hash.indexOf("/home") === -1) {
      if (hash.indexOf("details") !== -1 || hash.indexOf("search") !== -1 || hash.indexOf("settings") !== -1 || hash.indexOf("dashboard") !== -1 || hash.indexOf("video") !== -1) {
        return false;
      }
    }
    if (indexPage && (indexPage.classList.contains("hide") || indexPage.hidden)) return false;
    return true;
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
          if (action === "pause") {
            clearSpotlightBackdrop();
          } else if (action === "resume" && currentBackdropUrl) {
            setSpotlightBackdrop(currentBackdropUrl);
          }
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

function findHomeTab() {
    var homeTab = document.querySelector("#homeTab");
    if (homeTab && homeTab.isConnected) return homeTab;

    var indexPage = document.querySelector("#indexPage");
    if (indexPage && indexPage.isConnected) {
      var tab = indexPage.querySelector("#homeTab, .pageTabContent.is-active, .tabContent.is-active");
      if (tab) return tab;
      var sec = indexPage.querySelector(".sections, .homeSectionsContainer");
      if (sec && sec.parentElement) return sec.parentElement;
      return indexPage;
    }

    var activeTab = document.querySelector(".pageTabContent.is-active, div[data-role='page']:not(.hide) .homeSectionsContainer");
    if (activeTab) return activeTab.closest(".pageTabContent, div[data-role='page']") || activeTab;

    return null;
  }

  function installSpotlight() {
    var installed = false;
    safe(function () {
      var hash = window.location.hash || "";
      if (hash.indexOf("dashboard") !== -1 || hash.indexOf("settings") !== -1 || hash.indexOf("video") !== -1) {
        clearSpotlightLifecycle();
        return;
      }

      var homeTab = findHomeTab();
      if (!homeTab) {
        return;
      }

      var indexPage = homeTab.closest("#indexPage, div[data-role='page'], .page") || homeTab;
      var favoritesTab = document.querySelector("#favoritesTab");

      installFrameStyle();
      installBackdropOverlay();

      var iframe = homeTab.querySelector ? homeTab.querySelector("." + FRAME_CLASS) : null;
      if (!iframe) {
        iframe = document.querySelector("." + FRAME_CLASS);
      }

      if (!iframe) {
        iframe = document.createElement("iframe");
        iframe.className = FRAME_CLASS + " focusable";
        iframe.setAttribute("tabindex", "0");
        iframe.src = spotlightUrl;
        iframe.title = "Abyss Spotlight";
        iframe.style.width = "100%";
        iframe.style.display = "block";
        iframe.style.border = "none";
        iframe.addEventListener("blur", function () { spotlightFocused = false; });
        var sections = homeTab.querySelector ? homeTab.querySelector(".sections, .homeSectionsContainer") : null;
        homeTab.insertBefore(iframe, sections || homeTab.firstChild);
      } else if (iframe.parentElement !== homeTab) {
        var sections = homeTab.querySelector ? homeTab.querySelector(".sections, .homeSectionsContainer") : null;
        homeTab.insertBefore(iframe, sections || homeTab.firstChild);
      }

      iframe.style.display = "block";
      iframe.style.visibility = "visible";
      iframe.style.opacity = "1";
      document.documentElement.classList.add("abyss-spotlight-visible");

      if (indexPage && indexPage.classList) indexPage.classList.add("abyss-spotlight-active");
      if (homeTab.classList) homeTab.classList.add("abyss-spotlight-active");

      if (
        indexPage !== currentIndexPage ||
        homeTab !== currentHomeTab ||
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
        if (el) {
          el.style.display = "none";
          el.style.visibility = "hidden";
          el.style.pointerEvents = "none";
          el.style.width = "0";
          el.style.height = "0";
          el.style.opacity = "0";
        }
      }
    });
  }

  function installClaudeMenuIcon() {
    safe(function () {
      var btns = document.querySelectorAll(
        'button[aria-label="Menu"], button[aria-label="menu"], ' +
        'button:has(svg[data-testid="MenuIcon"]), svg[data-testid="MenuIcon"], ' +
        '.claude-stepped-menu, .mainDrawerButton, .headerButtonMenu, .headerLeft'
      );
      for (var i = 0; i < btns.length; i++) {
        btns[i].style.display = "none";
        btns[i].style.visibility = "hidden";
        btns[i].style.pointerEvents = "none";
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

  var enhanceTimeout = null;
  function debouncedEnhanceLibraryCards() {
    if (enhanceTimeout) clearTimeout(enhanceTimeout);
    enhanceTimeout = setTimeout(function () {
      enhanceLibraryCards();
    }, 400);
  }

  var libIds = { movies: "f137a2dd21bbc1b99aa5c0f6bf02a805", tvshows: "767bffe4f11c93ef34b805451a696a4e" };
  var librariesDiscovered = false;

  function discoverLibraries() {
    if (librariesDiscovered) return;
    try {
      if (window.ApiClient && typeof window.ApiClient.getCurrentUserId === "function") {
        var uid = window.ApiClient.getCurrentUserId();
        if (!uid) return;
        window.ApiClient.getUserViews(uid).then(function (res) {
          if (res && res.Items) {
            librariesDiscovered = true;
            res.Items.forEach(function (it) {
              var name = (it.Name || "").toLowerCase();
              var type = (it.CollectionType || "").toLowerCase();
              if (type === "movies" || name.indexOf("movie") !== -1) {
                libIds.movies = it.Id;
              } else if (type === "tvshows" || type === "series" || name.indexOf("show") !== -1 || name.indexOf("tv") !== -1 || name.indexOf("series") !== -1) {
                libIds.tvshows = it.Id;
              }
            });
          }
        }).catch(function () {});
      }
    } catch (e) {}
  }

  function navigateCategory(name) {
    if (name === "Home") {
      if (window.Emby && window.Emby.Page && typeof window.Emby.Page.show === "function") {
        window.Emby.Page.show("/home");
      } else {
        window.location.hash = "#/home";
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    var targetId = name === "Movies" ? libIds.movies : libIds.tvshows;
    if (targetId) {
      var links = document.querySelectorAll('a[href*="' + targetId + '"], [data-id="' + targetId + '"]');
      if (links.length && links[0].click) {
        links[0].click();
        return;
      }
      var targetUrl = "/details?id=" + targetId;
      if (window.Emby && window.Emby.Page && typeof window.Emby.Page.show === "function") {
        window.Emby.Page.show(targetUrl);
        return;
      }
      window.location.hash = "#" + targetUrl;
      return;
    }
    window.location.hash = name === "Movies" ? "#/movies" : "#/shows";
  }

  function updateActiveNavTab() {
    var hash = window.location.hash || "";
    var links = document.querySelectorAll(".apex-tv-tab, .apex-nav-item");
    for (var i = 0; i < links.length; i++) {
      var item = links[i];
      var navType = item.getAttribute("data-nav");
      var isActive = false;
      if (navType === "Home" && (!hash || hash.indexOf("/home") !== -1 || hash === "#/" || hash === "#")) {
        isActive = true;
      } else if (navType === "Movies" && (hash.indexOf("movie") !== -1 || (libIds.movies && hash.indexOf(libIds.movies) !== -1))) {
        isActive = true;
      } else if (navType === "TV Shows" && (hash.indexOf("show") !== -1 || hash.indexOf("series") !== -1 || hash.indexOf("tv") !== -1 || (libIds.tvshows && hash.indexOf(libIds.tvshows) !== -1))) {
        isActive = true;
      }
      if (isActive) item.classList.add("active");
      else item.classList.remove("active");
    }
  }

  function findActiveToolbar() {
    return document.querySelector(
      "header.MuiAppBar-root > .MuiToolbar-root, " +
      "header > .MuiToolbar-root, " +
      ".skinHeader .headerTop, " +
      ".headerTop, " +
      "header.MuiAppBar-root, " +
      ".skinHeader, " +
      "header"
    );
  }

  
  // ========================================================
  // AUTOMATIC CARD DEDUPLICATION & FALLBACK ART ENRICHMENT
  // ========================================================
  function deduplicateAndEnrichCards() {
    try {
      // 1. Safe non-destructive deduplication for library & home rails
      var containers = document.querySelectorAll('.itemsContainer, .verticalSection .cardBoxParent, .section1, .section2, .section3, .section4, .section5, .section6, .section7');
      containers.forEach(function(container) {
        if (container.closest('#itemDetailPage') || container.closest('.detailPagePrimaryContainer')) return;
        var cards = container.querySelectorAll('.card');
        if (!cards || !cards.length) return;
        var seen = {};
        cards.forEach(function(card) {
          var titleEl = card.querySelector('.cardText-first, .cardTitle, .cardText');
          if (!titleEl) return;
          var rawTitle = titleEl.textContent.trim();
          var key = rawTitle.toLowerCase().replace(/[^a-z0-9]/g, '');
          if (!key) return;

          var cic = card.querySelector('.cardImageContainer');
          var bg = cic ? (cic.style.backgroundImage || '') : '';
          var hasImg = !!card.querySelector('img[src]:not([src=""])') ||
                       (bg.indexOf('url(') !== -1) ||
                       (cic && (cic.getAttribute('data-src') || cic.getAttribute('data-image-url') || cic.classList.contains('lazy-image-fadein-fast')));

          if (seen[key]) {
            if (hasImg && !seen[key].hasImg) {
              seen[key].card.style.display = 'none';
              seen[key].card.classList.add('hide', 'apex-dup-hidden');
              seen[key] = { card: card, hasImg: hasImg };
            } else {
              card.style.display = 'none';
              card.classList.add('hide', 'apex-dup-hidden');
            }
          } else {
            seen[key] = { card: card, hasImg: hasImg };
          }
        });
      });

      // Purge any stray fallback art elements so real posters are never obstructed
      var oldFallbacks = document.querySelectorAll('.apex-fallback-art');
      for (var of = 0; of < oldFallbacks.length; of++) {
        oldFallbacks[of].style.setProperty("display", "none", "important");
      }
    } catch (e) {}
  }

  function ensureTopNavigation() {
    safe(function () {
      discoverLibraries();

      // 1. Mount or verify #apex-tv-topbar directly on document.body (immune to React wiping)
      var tvTopbar = document.getElementById("apex-tv-topbar");
      if (!tvTopbar && document.body) {
        tvTopbar = document.createElement("div");
        tvTopbar.id = "apex-tv-topbar";
        tvTopbar.className = "apex-tv-topbar";

        var tabsContainer = document.createElement("div");
        tabsContainer.className = "apex-tv-tabs";

        var categories = [
          { label: "Home", name: "Home" },
          { label: "Movies", name: "Movies" },
          { label: "TV Shows", name: "TV Shows" }
        ];

        categories.forEach(function (cat) {
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "apex-tv-tab";
          btn.textContent = cat.label;
          btn.setAttribute("data-nav", cat.name);
          btn.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            var all = document.querySelectorAll(".apex-tv-tab, .apex-nav-item");
            for (var a = 0; a < all.length; a++) all[a].classList.remove("active");
            btn.classList.add("active");
            navigateCategory(cat.name);
          });
          tabsContainer.appendChild(btn);
        });

        tvTopbar.appendChild(tabsContainer);
        document.body.appendChild(tvTopbar);
      }

      if (tvTopbar) {
        var activePage = document.querySelector(".page:not(.hide), .view:not(.hide)");
        var activeId = activePage ? activePage.id : "";
        var hash = (window.location.hash || "").toLowerCase();

        var isVideo = !!document.querySelector(".videoPlayerContainer:not(.hide), #videoOsdPage:not(.hide)");
        var isMismatch = !!document.querySelector("#serverMismatchPage:not(.hide), .serverMismatchPage:not(.hide)");
        var isAuthScreen = !!document.querySelector("#loginPage:not(.hide), .loginPage:not(.hide), #selectServerPage:not(.hide), .selectServerPage:not(.hide)");
        var isAuthRoute = hash.indexOf("login") !== -1 || hash.indexOf("selectserver") !== -1 || hash.indexOf("servermismatch") !== -1 || hash.indexOf("forgotpassword") !== -1;
        var isDetailPage = activeId === "itemDetailPage" || !!document.querySelector("#itemDetailPage:not(.hide), .itemDetailPage:not(.hide)") || hash.indexOf("details") !== -1;
        var isSettingsRoute = hash.indexOf("dashboard") !== -1 || hash.indexOf("settings") !== -1;

        var isCatalog = activeId === "indexPage" || activeId === "moviesPage" || activeId === "tvShowsPage" ||
                        !!document.querySelector("#indexPage:not(.hide), .homePage:not(.hide), #moviesPage:not(.hide), #tvShowsPage:not(.hide), .libraryPage:not(.hide), #homeTab, .itemsContainer:not(.hide)");

        if (isVideo || isMismatch || isAuthScreen || isAuthRoute || isDetailPage || isSettingsRoute || !isCatalog) {
          tvTopbar.classList.remove("is-visible");
          document.body.classList.remove("show-apex-topbar");
          tvTopbar.style.display = "none";
          tvTopbar.style.visibility = "hidden";
        } else {
          tvTopbar.classList.add("is-visible");
          document.body.classList.add("show-apex-topbar");
          tvTopbar.style.display = "flex";
          tvTopbar.style.visibility = "visible";
          tvTopbar.style.opacity = "1";
        }
      }

            // 1.4 Guarantee strictly one poster on #itemDetailPage
      // 1.4 Guarantee strictly one poster on #itemDetailPage without breaking DOM references
      var detailPosters = document.querySelectorAll('#itemDetailPage .detailPagePrimaryContainer .detailImageContainer');
      if (detailPosters.length > 1) {
        for (var dp = 1; dp < detailPosters.length; dp++) {
          detailPosters[dp].style.setProperty('display', 'none', 'important');
        }
      }
      // Never remove .detailLogo from DOM - Jellyfin itemDetails.chunk.js requires it for classList operations

      deduplicateAndEnrichCards();

      // 1.5 Suppress and purge floating Play / Shuffle buttons from catalog/library views
      var strayPlayBtns = document.querySelectorAll(
        ':is(.view, .page, [data-role="page"], .libraryPage):not(#itemDetailPage):not(#videoOsdPage) :is(.btnPlay, .btnShuffle, button[data-action="playall"], button[data-action="shuffleall"], button[title*="Play all" i], button[title*="Shuffle all" i]), ' +
        '.viewSettings :is(.btnPlay, .btnShuffle, button[data-action="play"], button[data-action="shuffle"]), ' +
        '.pageTitleWithDefaultButton :is(.btnPlay, .btnShuffle), ' +
        '.mainTabsContainer :is(.btnPlay, .btnShuffle)'
      );
      for (var sp = 0; sp < strayPlayBtns.length; sp++) {
        strayPlayBtns[sp].style.setProperty("display", "none", "important");
        strayPlayBtns[sp].classList.add("hide");
      }

      // 2. Hide Hamburger, Cast, SyncPlay, and stray drawer buttons completely
      var unwanted = document.querySelectorAll(
        'button[aria-label="Menu"], button[aria-label="menu"], ' +
        'button:has(svg[data-testid="MenuIcon"]), svg[data-testid="MenuIcon"], .claude-stepped-menu, ' +
        '.mainDrawerButton, .headerButtonMenu, .headerSyncplayButton, .btnSyncPlay, ' +
        '.headerCastButton, .btnCast, button[data-action="cast"], button[data-action="syncplay"], ' +
        'button[title*="SyncPlay" i], button[aria-label*="SyncPlay" i], button[title*="Cast" i], button[aria-label*="Cast" i], ' +
        'button:has(svg[data-testid="CastIcon"]), button:has(svg[data-testid="GroupIcon"]), button:has(svg[data-testid="PeopleIcon"]), ' +
        '.headerTop .pageTitle, .skinHeader .pageTitle, .headerLogoText, .pageTitleWithDefaultLogo, .headerTabs, .sectionTabs, .headerTabs.sectionTabs, .emby-tabs, .emby-tabs-slider'
      );
      for (var u = 0; u < unwanted.length; u++) {
        unwanted[u].style.display = "none";
        unwanted[u].style.visibility = "hidden";
        unwanted[u].style.pointerEvents = "none";
      }

      // Handle Back Button: Hidden on Home, Visible & clickable on interior library/detail pages
      var currentHash = window.location.hash || "";
      var isHomeRoute = !currentHash || currentHash === "#" || currentHash === "#/" || currentHash.indexOf("/home") !== -1;
      var backBtns = document.querySelectorAll(".headerBackButton, [data-action='back']");
      for (var b = 0; b < backBtns.length; b++) {
        if (isHomeRoute) {
          backBtns[b].style.display = "none";
        } else {
          backBtns[b].style.display = "inline-flex";
          backBtns[b].style.visibility = "visible";
          backBtns[b].style.pointerEvents = "auto";
        }
      }

      updateActiveNavTab();
      normalizeContinueWatchingCards();
      deduplicateDomCards();

      // 3. Ensure Search Pill in landscape & desktop
      var bar = findActiveToolbar();
      if (bar) {
        var headerRight = bar.querySelector(".headerRight, .MuiBox-root:last-of-type, .MuiStack-root:last-of-type") || bar;
        if (headerRight && !bar.querySelector(".apex-search-pill")) {
          var searchPill = document.createElement("button");
          searchPill.type = "button";
          searchPill.className = "apex-search-pill";
          searchPill.setAttribute("aria-label", "Search");
          searchPill.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg><span>Search</span>';
          searchPill.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            var nativeSearch = document.querySelector('.headerSearchButton, [data-action="search"], button[title*="Search" i]');
            if (nativeSearch && nativeSearch.click) {
              nativeSearch.click();
            } else {
              window.location.hash = "#/search";
            }
          });
          var userBtn = headerRight.querySelector(".headerUserButtonRound, .headerButton-user, button[aria-label*='user' i], button[aria-label*='profile' i]");
          if (userBtn) {
            headerRight.insertBefore(searchPill, userBtn);
          } else {
            headerRight.insertBefore(searchPill, headerRight.firstChild);
          }
        }
      }
    });
  }

  
  function normalizeContinueWatchingCards() {
    safe(function () {
      var resumeContainers = document.querySelectorAll('.resumeSection, .nextUpSection, div[data-category="resume"], div[data-category="nextup"], #indexPage .itemsContainer-slider');
      for (var rc = 0; rc < resumeContainers.length; rc++) {
        var cards = resumeContainers[rc].querySelectorAll('.card');
        for (var c = 0; c < cards.length; c++) {
          var card = cards[c];
          card.classList.remove('backdropCard', 'overflowBackdropCard', 'smallBackdropCard');
          card.classList.add('portraitCard');
          card.style.width = '140px';
          card.style.maxWidth = '140px';
          card.style.minWidth = '140px';
          card.style.flex = '0 0 140px';
          
          var padders = card.querySelectorAll('.cardPadder');
          for (var p = 0; p < padders.length; p++) {
            padders[p].classList.remove('cardPadder-backdrop', 'cardPadder-overflowBackdrop', 'cardPadder-smallBackdrop');
            padders[p].classList.add('cardPadder-portrait');
            padders[p].style.paddingBottom = '150%';
            padders[p].style.aspectRatio = '2 / 3';
            padders[p].style.height = '0';
          }

          var scalables = card.querySelectorAll('.cardScalable');
          for (var s = 0; s < scalables.length; s++) {
            scalables[s].style.aspectRatio = '2 / 3';
            scalables[s].style.borderRadius = '12px';
            scalables[s].style.overflow = 'hidden';
          }

          var imgs = card.querySelectorAll('.cardImageContainer img');
          for (var m = 0; m < imgs.length; m++) {
            imgs[m].style.objectFit = 'cover';
            imgs[m].style.width = '100%';
            imgs[m].style.height = '100%';
            imgs[m].style.position = 'absolute';
            imgs[m].style.top = '0';
            imgs[m].style.left = '0';
          }
        }
      }
    });
  }

  function deduplicateDomCards() {
    safe(function () {
      var activePage = document.querySelector('.page:not(.hide), .view:not(.hide), [data-role="page"]:not(.hide)') || document;
      var cards = activePage.querySelectorAll('.card');
      if (!cards || !cards.length) return;
      var seenTitles = {};
      for (var j = 0; j < cards.length; j++) {
        var card = cards[j];
        if (!card.classList || !card.classList.contains("card")) continue;
        if (card.closest('#itemDetailPage') || card.closest('.detailImageContainer')) continue;
        var titleEl = card.querySelector(".cardText-first") || card.querySelector(".cardText:not(.cardText-secondary)") || card.querySelector(".cardTextCentered") || card.querySelector(".cardText");
        var rawTitle = (titleEl ? titleEl.textContent : (card.getAttribute("aria-label") || "")).trim().toLowerCase();
        var normTitle = rawTitle.replace(/\s*\(\s*\d{4}\s*\)\s*/g, "").replace(/^(linkz|the)\b/g, "").replace(/[^a-z0-9]/g, "");
        if (!normTitle) continue;
        if (seenTitles[normTitle]) {
          card.classList.add("apex-duplicate-hidden");
          card.style.setProperty("display", "none", "important");
          card.style.setProperty("visibility", "hidden", "important");
          card.style.setProperty("width", "0px", "important");
          card.style.setProperty("height", "0px", "important");
          card.style.setProperty("flex", "0 0 0px", "important");
          card.style.setProperty("margin", "0px", "important");
          card.style.setProperty("padding", "0px", "important");
        } else {
          seenTitles[normTitle] = true;
        }
      }
    });
  }

  var topNavGuardianTimer = null;
  function startTopNavGuardian() {
    if (topNavGuardianTimer) clearInterval(topNavGuardianTimer);
    topNavGuardianTimer = setInterval(ensureTopNavigation, 400);
    window.addEventListener("hashchange", ensureTopNavigation);
    window.addEventListener("popstate", ensureTopNavigation);
    window.addEventListener("pageshow", ensureTopNavigation);
    document.addEventListener("viewshow", ensureTopNavigation);
  }
  startTopNavGuardian();

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
      ensureTopNavigation();
        replaceServerNameText();
        installSpatialDpadNavigation();
        debouncedEnhanceLibraryCards();
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
      ensureTopNavigation();
    replaceServerNameText();
    installSpatialDpadNavigation();
    debouncedEnhanceLibraryCards();
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
          var observerTimeout = null;
          var observer = new MutationObserver(function () {
            if (observerTimeout) return;
            observerTimeout = setTimeout(function () {
              observerTimeout = null;
              scheduleInstall();
            }, 250);
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
      ensureTopNavigation();
      replaceServerNameText();
      installSpatialDpadNavigation();
      debouncedEnhanceLibraryCards();
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