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
    '<svg class="apex-delta-icon" viewBox="215 376 1460 1460" width="28" height="28" style="display:inline-block;vertical-align:middle;max-width:32px;max-height:32px;object-fit:contain;" aria-label="Apex">' +
    '<path d="M 1502.4 446.5 L 1491.9 446.5 L 1488.4 443.0 L 1439.4 443.0 L 1435.9 446.5 L 1425.4 446.5 L 1421.9 450.0 L 1411.3 450.0 L 1400.8 457.0 L 1390.3 457.0 L 1386.8 460.5 L 1379.8 460.5 L 1376.3 464.0 L 1369.3 464.0 L 1365.8 467.5 L 1358.8 467.5 L 1355.3 471.0 L 1348.3 471.0 L 1344.8 474.5 L 1337.8 474.5 L 1334.3 478.0 L 1327.3 478.0 L 1323.8 481.5 L 1316.8 481.5 L 1313.3 485.0 L 1306.3 485.0 L 1302.7 488.5 L 1295.7 488.5 L 1292.2 492.1 L 1285.2 492.1 L 1281.7 495.6 L 1274.7 495.6 L 1271.2 499.1 L 1264.2 499.1 L 1253.7 506.1 L 1243.2 506.1 L 1239.7 509.6 L 1232.7 509.6 L 1229.2 513.1 L 1222.2 513.1 L 1218.7 516.6 L 1211.7 516.6 L 1201.2 523.6 L 1194.1 523.6 L 1190.6 527.1 L 1180.1 527.1 L 1169.6 534.1 L 1162.6 534.1 L 1159.1 537.6 L 1148.6 537.6 L 1138.1 544.6 L 1127.6 544.6 L 1124.1 548.1 L 1117.1 548.1 L 1113.6 551.6 L 1110.1 551.6 L 1106.6 555.1 L 1096.1 555.1 L 1085.6 562.1 L 1078.5 562.1 L 1075.0 565.6 L 1064.5 565.6 L 1054.0 572.6 L 1047.0 572.6 L 1043.5 576.1 L 1033.0 576.1 L 1022.5 583.1 L 1015.5 583.1 L 1012.0 586.6 L 1001.5 586.6 L 991.0 593.6 L 984.0 593.6 L 980.5 597.1 L 969.9 597.1 L 966.4 600.6 L 959.4 600.6 L 955.9 604.2 L 952.4 604.2 L 948.9 607.7 L 941.9 607.7 L 938.4 611.2 L 931.4 611.2 L 927.9 614.7 L 917.4 614.7 L 906.9 621.7 L 899.9 621.7 L 896.4 625.2 L 889.4 625.2 L 885.9 628.7 L 878.9 628.7 L 875.4 632.2 L 868.4 632.2 L 864.9 635.7 L 857.8 635.7 L 854.3 639.2 L 847.3 639.2 L 843.8 642.7 L 836.8 642.7 L 833.3 646.2 L 822.8 646.2 L 812.3 653.2 L 805.3 653.2 L 801.8 656.7 L 794.8 656.7 L 791.3 660.2 L 784.3 660.2 L 780.8 663.7 L 773.8 663.7 L 770.3 667.2 L 763.3 667.2 L 759.8 670.7 L 752.8 670.7 L 749.2 674.2 L 742.2 674.2 L 738.7 677.7 L 731.7 677.7 L 728.2 681.2 L 721.2 681.2 L 717.7 684.7 L 710.7 684.7 L 707.2 688.2 L 700.2 688.2 L 696.7 691.7 L 689.7 691.7 L 686.2 695.2 L 679.2 695.2 L 675.7 698.7 L 668.7 698.7 L 665.2 702.2 L 658.2 702.2 L 654.7 705.7 L 647.7 705.7 L 644.2 709.2 L 637.1 709.2 L 633.6 712.7 L 626.6 712.7 L 623.1 716.3 L 616.1 716.3 L 612.6 719.8 L 605.6 719.8 L 602.1 723.3 L 595.1 723.3 L 591.6 726.8 L 584.6 726.8 L 581.1 730.3 L 574.1 730.3 L 570.6 733.8 L 563.6 733.8 L 560.1 737.3 L 553.1 737.3 L 549.6 740.8 L 542.6 740.8 L 539.1 744.3 L 532.1 744.3 L 528.5 747.8 L 521.5 747.8 L 518.0 751.3 L 511.0 751.3 L 507.5 754.8 L 500.5 754.8 L 497.0 758.3 L 490.0 758.3 L 486.5 761.8 L 479.5 761.8 L 476.0 765.3 L 469.0 765.3 L 465.5 768.8 L 458.5 768.8 L 455.0 772.3 L 448.0 772.3 L 444.5 775.8 L 437.5 775.8 L 434.0 779.3 L 427.0 779.3 L 423.5 782.8 L 416.4 782.8 L 412.9 786.3 L 405.9 786.3 L 402.4 789.8 L 395.4 789.8 L 391.9 793.3 L 384.9 793.3 L 381.4 796.8 L 374.4 796.8 L 363.9 803.8 L 360.4 803.8 L 353.4 810.8 L 349.9 810.8 L 342.9 817.8 L 339.4 817.8 L 318.4 838.9 L 318.4 842.4 L 307.9 852.9 L 307.9 856.4 L 304.3 859.9 L 304.3 863.4 L 297.3 873.9 L 297.3 880.9 L 290.3 891.4 L 290.3 905.4 L 286.8 908.9 L 286.8 958.0 L 290.3 961.5 L 290.3 972.0 L 293.8 975.5 L 293.8 982.5 L 297.3 986.0 L 297.3 993.0 L 304.3 1003.5 L 304.3 1007.0 L 311.4 1014.0 L 311.4 1017.5 L 325.4 1031.5 L 325.4 1035.0 L 335.9 1045.5 L 339.4 1045.5 L 346.4 1052.6 L 349.9 1052.6 L 356.9 1059.6 L 360.4 1059.6 L 363.9 1063.1 L 367.4 1063.1 L 370.9 1066.6 L 374.4 1066.6 L 377.9 1070.1 L 381.4 1070.1 L 384.9 1073.6 L 388.4 1073.6 L 398.9 1080.6 L 405.9 1080.6 L 409.4 1084.1 L 412.9 1084.1 L 416.4 1087.6 L 420.0 1087.6 L 423.5 1091.1 L 427.0 1091.1 L 437.5 1098.1 L 441.0 1098.1 L 451.5 1105.1 L 455.0 1105.1 L 458.5 1108.6 L 462.0 1108.6 L 469.0 1115.6 L 472.5 1115.6 L 476.0 1119.1 L 479.5 1119.1 L 483.0 1122.6 L 486.5 1122.6 L 493.5 1129.6 L 497.0 1129.6 L 500.5 1133.1 L 504.0 1133.1 L 507.5 1136.6 L 511.0 1136.6 L 518.0 1143.6 L 521.5 1143.6 L 528.5 1150.6 L 532.1 1150.6 L 539.1 1157.7 L 542.6 1157.7 L 546.1 1161.2 L 549.6 1161.2 L 560.1 1171.7 L 563.6 1171.7 L 570.6 1178.7 L 574.1 1178.7 L 581.1 1185.7 L 584.6 1185.7 L 595.1 1196.2 L 598.6 1196.2 L 609.1 1206.7 L 612.6 1206.7 L 623.1 1217.2 L 626.6 1217.2 L 640.7 1231.2 L 644.2 1231.2 L 665.2 1252.2 L 668.7 1252.2 L 693.2 1276.8 L 696.7 1276.8 L 700.2 1280.3 L 700.2 1283.8 L 703.7 1287.3 L 707.2 1287.3 L 763.3 1343.3 L 763.3 1346.8 L 791.3 1374.8 L 791.3 1378.3 L 805.3 1392.4 L 805.3 1395.9 L 822.8 1413.4 L 822.8 1416.9 L 833.3 1427.4 L 833.3 1430.9 L 843.8 1441.4 L 843.8 1444.9 L 854.3 1455.4 L 854.3 1458.9 L 861.3 1465.9 L 861.3 1469.4 L 868.4 1476.4 L 868.4 1479.9 L 875.4 1486.9 L 875.4 1490.5 L 882.4 1497.5 L 882.4 1501.0 L 889.4 1508.0 L 889.4 1511.5 L 892.9 1515.0 L 892.9 1518.5 L 899.9 1525.5 L 899.9 1529.0 L 903.4 1532.5 L 903.4 1536.0 L 910.4 1543.0 L 910.4 1546.5 L 913.9 1550.0 L 913.9 1553.5 L 920.9 1560.5 L 920.9 1564.0 L 924.4 1567.5 L 924.4 1571.0 L 927.9 1574.5 L 927.9 1578.0 L 931.4 1581.5 L 931.4 1585.0 L 934.9 1588.5 L 934.9 1592.0 L 938.4 1595.5 L 938.4 1599.0 L 941.9 1602.6 L 941.9 1606.1 L 948.9 1616.6 L 948.9 1620.1 L 952.4 1623.6 L 952.4 1627.1 L 955.9 1630.6 L 955.9 1634.1 L 959.4 1637.6 L 959.4 1641.1 L 966.4 1651.6 L 966.4 1658.6 L 973.5 1665.6 L 973.5 1672.6 L 977.0 1676.1 L 977.0 1679.6 L 980.5 1683.1 L 980.5 1686.6 L 987.5 1697.1 L 987.5 1700.6 L 991.0 1704.1 L 991.0 1707.6 L 1001.5 1718.2 L 1001.5 1721.7 L 1022.5 1742.7 L 1026.0 1742.7 L 1033.0 1749.7 L 1036.5 1749.7 L 1043.5 1756.7 L 1050.5 1756.7 L 1054.0 1760.2 L 1057.5 1760.2 L 1061.0 1763.7 L 1068.0 1763.7 L 1071.5 1767.2 L 1082.0 1767.2 L 1085.6 1770.7 L 1134.6 1770.7 L 1138.1 1767.2 L 1148.6 1767.2 L 1152.1 1763.7 L 1159.1 1763.7 L 1169.6 1756.7 L 1176.6 1756.7 L 1183.6 1749.7 L 1187.1 1749.7 L 1194.1 1742.7 L 1197.7 1742.7 L 1222.2 1718.2 L 1222.2 1714.7 L 1229.2 1707.6 L 1229.2 1704.1 L 1232.7 1700.6 L 1232.7 1697.1 L 1239.7 1686.6 L 1239.7 1679.6 L 1246.7 1669.1 L 1246.7 1662.1 L 1250.2 1658.6 L 1250.2 1651.6 L 1253.7 1648.1 L 1253.7 1641.1 L 1257.2 1637.6 L 1257.2 1630.6 L 1260.7 1627.1 L 1260.7 1620.1 L 1264.2 1616.6 L 1264.2 1609.6 L 1267.7 1606.1 L 1267.7 1599.0 L 1274.7 1588.5 L 1274.7 1578.0 L 1281.7 1567.5 L 1281.7 1557.0 L 1288.7 1546.5 L 1288.7 1539.5 L 1292.2 1536.0 L 1292.2 1529.0 L 1295.7 1525.5 L 1295.7 1518.5 L 1299.2 1515.0 L 1299.2 1508.0 L 1302.7 1504.5 L 1302.7 1497.5 L 1306.3 1494.0 L 1306.3 1486.9 L 1309.8 1483.4 L 1309.8 1476.4 L 1313.3 1472.9 L 1313.3 1465.9 L 1316.8 1462.4 L 1316.8 1455.4 L 1320.3 1451.9 L 1320.3 1444.9 L 1323.8 1441.4 L 1323.8 1434.4 L 1327.3 1430.9 L 1327.3 1423.9 L 1330.8 1420.4 L 1330.8 1413.4 L 1334.3 1409.9 L 1334.3 1402.9 L 1337.8 1399.4 L 1337.8 1392.4 L 1341.3 1388.9 L 1341.3 1381.9 L 1344.8 1378.3 L 1344.8 1371.3 L 1351.8 1360.8 L 1351.8 1353.8 L 1355.3 1350.3 L 1355.3 1343.3 L 1358.8 1339.8 L 1358.8 1332.8 L 1362.3 1329.3 L 1362.3 1322.3 L 1365.8 1318.8 L 1365.8 1311.8 L 1369.3 1308.3 L 1369.3 1301.3 L 1372.8 1297.8 L 1372.8 1290.8 L 1376.3 1287.3 L 1376.3 1280.3 L 1379.8 1276.8 L 1379.8 1269.8 L 1383.3 1266.2 L 1383.3 1259.2 L 1386.8 1255.7 L 1386.8 1248.7 L 1390.3 1245.2 L 1390.3 1238.2 L 1393.8 1234.7 L 1393.8 1227.7 L 1397.3 1224.2 L 1397.3 1217.2 L 1404.3 1206.7 L 1404.3 1199.7 L 1407.8 1196.2 L 1407.8 1185.7 L 1414.8 1175.2 L 1414.8 1168.2 L 1418.4 1164.7 L 1418.4 1157.7 L 1421.9 1154.1 L 1421.9 1147.1 L 1425.4 1143.6 L 1425.4 1136.6 L 1428.9 1133.1 L 1428.9 1126.1 L 1432.4 1122.6 L 1432.4 1115.6 L 1435.9 1112.1 L 1435.9 1105.1 L 1439.4 1101.6 L 1439.4 1094.6 L 1442.9 1091.1 L 1442.9 1084.1 L 1446.4 1080.6 L 1446.4 1073.6 L 1449.9 1070.1 L 1449.9 1063.1 L 1453.4 1059.6 L 1453.4 1052.6 L 1460.4 1042.0 L 1460.4 1031.5 L 1467.4 1021.0 L 1467.4 1014.0 L 1470.9 1010.5 L 1470.9 1003.5 L 1474.4 1000.0 L 1474.4 989.5 L 1481.4 979.0 L 1481.4 972.0 L 1484.9 968.5 L 1484.9 961.5 L 1488.4 958.0 L 1488.4 951.0 L 1491.9 947.5 L 1491.9 940.5 L 1495.4 937.0 L 1495.4 929.9 L 1498.9 926.4 L 1498.9 919.4 L 1502.4 915.9 L 1502.4 908.9 L 1509.4 898.4 L 1509.4 887.9 L 1512.9 884.4 L 1512.9 877.4 L 1516.4 873.9 L 1516.4 866.9 L 1523.4 856.4 L 1523.4 849.4 L 1526.9 845.9 L 1526.9 835.4 L 1534.0 824.9 L 1534.0 817.8 L 1537.5 814.3 L 1537.5 807.3 L 1541.0 803.8 L 1541.0 796.8 L 1544.5 793.3 L 1544.5 786.3 L 1548.0 782.8 L 1548.0 775.8 L 1551.5 772.3 L 1551.5 765.3 L 1555.0 761.8 L 1555.0 754.8 L 1558.5 751.3 L 1558.5 744.3 L 1562.0 740.8 L 1562.0 733.8 L 1565.5 730.3 L 1565.5 723.3 L 1569.0 719.8 L 1569.0 712.7 L 1572.5 709.2 L 1572.5 702.2 L 1576.0 698.7 L 1576.0 691.7 L 1579.5 688.2 L 1579.5 681.2 L 1586.5 670.7 L 1586.5 663.7 L 1590.0 660.2 L 1590.0 653.2 L 1593.5 649.7 L 1593.5 642.7 L 1597.0 639.2 L 1597.0 632.2 L 1600.5 628.7 L 1600.5 618.2 L 1604.0 614.7 L 1604.0 551.6 L 1600.5 548.1 L 1600.5 541.1 L 1597.0 537.6 L 1597.0 534.1 L 1593.5 530.6 L 1593.5 527.1 L 1590.0 523.6 L 1590.0 516.6 L 1583.0 509.6 L 1583.0 506.1 L 1572.5 495.6 L 1572.5 492.1 L 1558.5 478.0 L 1555.0 478.0 L 1541.0 464.0 L 1537.5 464.0 L 1534.0 460.5 L 1530.5 460.5 L 1526.9 457.0 L 1523.4 457.0 L 1512.9 450.0 L 1505.9 450.0 Z" fill="#ffffff"/>' +
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

      // 2. Direct <img> replacements for all Jellyfin / icon-transparent references
      var targetImgs = document.querySelectorAll(
        'img[src*="icon-transparent"], img[src*="jellyfin"], img[src*="touchicon"], .adminDrawerLogo img, .headerLogo img, .MuiButton-startIcon img, .mainDrawer a[to="/"] img, .mainDrawer a[href="/"] img'
      );
      for (var k = 0; k < targetImgs.length; k++) {
        var imgEl = targetImgs[k];
        if (imgEl.src && !imgEl.src.includes("apex-logo")) {
          imgEl.src = logoSvgUrl;
          imgEl.srcset = "";
        }
      }

      // 3. Header and Drawer Logos - replace any default icons or SVGs with our exact Apex Delta glyph
      var logos = document.querySelectorAll(
        ".imgLogoIcon, .adminDrawerLogo img, .adminDrawerLogo, .headerLogo, .pageTitleWithDefaultLogo, .btnSelectServer .navMenuOptionIcon"
      );
      for (var j = 0; j < logos.length; j++) {
        var el = logos[j];
        if (el.tagName.toLowerCase() === "img") {
          if (el.src && !el.src.includes("apex-logo")) {
            el.src = logoSvgUrl;
          }
        } else if (!el.querySelector(".apex-delta-icon")) {
          el.innerHTML = APEX_DELTA_SVG;
        }
      }

      // 4. Drawer top card logo icon
      var drawerServerOption = document.querySelector(".mainDrawer a[to='/'], .mainDrawer a[href='/'], .mainDrawer .btnSelectServer, .mainDrawer .navMenuOption:first-child");
      if (drawerServerOption) {
        var drawerImg = drawerServerOption.querySelector('img[src*="icon-transparent"], img');
        if (drawerImg && !drawerImg.src.includes("apex-logo")) {
          drawerImg.src = logoSvgUrl;
        }
      }

      // 5. Login Page top icon & startIcon
      var loginHeader = document.querySelector("#loginPage .headerLogo, .skinHeader .headerLogo, .skinHeader .pageTitleWithDefaultLogo, .MuiButton-startIcon");
      if (loginHeader) {
        var startImg = loginHeader.querySelector("img");
        if (startImg && !startImg.src.includes("apex-logo")) {
          startImg.src = logoSvgUrl;
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