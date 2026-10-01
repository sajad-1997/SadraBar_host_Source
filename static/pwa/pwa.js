(() => {
  "use strict";

  let deferredPrompt = null;
  let registrationRef = null;
  let refreshing = false;

  const state = {
    installDismissedAt: Number(localStorage.getItem("pwa_install_dismissed_at") || 0),
  };

  function isStandalone() {
    return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  }

  function canShowInstallCard() {
    const dismissedRecently = Date.now() - state.installDismissedAt < 7 * 24 * 60 * 60 * 1000;
    return Boolean(deferredPrompt) && !isStandalone() && !dismissedRecently;
  }

  function ensureInstallCard() {
    let card = document.getElementById("pwa-install-card");
    if (card) {
      return card;
    }

    card = document.createElement("section");
    card.id = "pwa-install-card";
    card.className = "pwa-install-card";
    card.setAttribute("aria-live", "polite");
    card.innerHTML = [
      '<div>',
      '<h2 class="pwa-install-title">نصب اپلیکیشن صدرابار</h2>',
      '<p class="pwa-install-text">برای دسترسی سریع، اجرای تمام صفحه و استفاده بهتر در موبایل، نسخه PWA را نصب کنید.</p>',
      '</div>',
      '<div class="pwa-install-actions">',
      '<button type="button" class="pwa-button pwa-button-primary" data-pwa-install>نصب</button>',
      '<button type="button" class="pwa-button pwa-button-ghost" data-pwa-dismiss>بعدا</button>',
      '</div>',
    ].join("");

    card.querySelector("[data-pwa-install]").addEventListener("click", install);
    card.querySelector("[data-pwa-dismiss]").addEventListener("click", dismissInstall);
    document.body.appendChild(card);
    return card;
  }

  function showInstallCard() {
    const card = ensureInstallCard();
    card.classList.toggle("is-visible", canShowInstallCard());
  }

  function hideInstallCard() {
    const card = document.getElementById("pwa-install-card");
    if (card) {
      card.classList.remove("is-visible");
    }
  }

  async function install() {
    if (!deferredPrompt) {
      showIosInstallHint();
      return null;
    }

    deferredPrompt.prompt();
    const choice = await deferredPrompt.userChoice;
    deferredPrompt = null;
    hideInstallCard();
    return choice;
  }

  function dismissInstall() {
    state.installDismissedAt = Date.now();
    localStorage.setItem("pwa_install_dismissed_at", String(state.installDismissedAt));
    hideInstallCard();
  }

  function showIosInstallHint() {
    if (!/iphone|ipad|ipod/i.test(navigator.userAgent) || isStandalone()) {
      return;
    }
    window.alert("در iOS از دکمه Share مرورگر، گزینه Add to Home Screen را انتخاب کنید.");
  }

  function ensureOfflineBanner() {
    let banner = document.getElementById("pwa-offline-banner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "pwa-offline-banner";
      banner.className = "pwa-offline-banner";
      banner.setAttribute("role", "status");
      banner.textContent = "اتصال اینترنت قطع است. اطلاعات ذخیره شده نمایش داده می شود.";
      document.body.appendChild(banner);
    }
    return banner;
  }

  function updateOnlineStatus() {
    ensureOfflineBanner().classList.toggle("is-visible", !navigator.onLine);
  }

  function showUpdateBanner(worker) {
    let banner = document.getElementById("pwa-update-banner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "pwa-update-banner";
      banner.className = "pwa-update-banner";
      banner.innerHTML = '<span>نسخه تازه آماده است.</span><button type="button">به روزرسانی</button>';
      document.body.appendChild(banner);
    }

    banner.querySelector("button").onclick = () => {
      worker.postMessage({ type: "SKIP_WAITING" });
    };
    banner.classList.add("is-visible");
  }

  function trackInstallingWorker(worker) {
    if (!worker) {
      return;
    }
    worker.addEventListener("statechange", () => {
      if (worker.state === "installed" && navigator.serviceWorker.controller) {
        showUpdateBanner(worker);
      }
    });
  }

  async function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) {
      return null;
    }

    registrationRef = await navigator.serviceWorker.register("/sw.js", { scope: "/" });
    trackInstallingWorker(registrationRef.installing);
    registrationRef.addEventListener("updatefound", () => {
      trackInstallingWorker(registrationRef.installing);
    });

    setInterval(() => {
      registrationRef.update();
    }, 60 * 60 * 1000);

    return registrationRef;
  }

  function requestNotificationPermission() {
    if (!("Notification" in window)) {
      return Promise.resolve("unsupported");
    }
    if (Notification.permission !== "default") {
      return Promise.resolve(Notification.permission);
    }
    return Notification.requestPermission();
  }

  async function sendNotification(title, options = {}) {
    const permission = await requestNotificationPermission();
    if (permission !== "granted") {
      return false;
    }

    const payload = {
      body: options.body || "پیام جدید از سامانه صدرابار",
      icon: options.icon || "/static/pwa/icons/icon-192x192.png",
      badge: "/static/pwa/icons/icon-72x72.png",
      dir: "rtl",
      lang: "fa-IR",
      data: { url: options.url || "/" },
      tag: options.tag || "sadrabar-local",
    };

    if (registrationRef && registrationRef.showNotification) {
      await registrationRef.showNotification(title || "صدرابار", payload);
      return true;
    }

    new Notification(title || "صدرابار", payload);
    return true;
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredPrompt = event;
    showInstallCard();
  });

  window.addEventListener("appinstalled", () => {
    deferredPrompt = null;
    hideInstallCard();
  });

  window.addEventListener("online", updateOnlineStatus);
  window.addEventListener("offline", updateOnlineStatus);

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (refreshing) {
        return;
      }
      refreshing = true;
      window.location.reload();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (isStandalone()) {
      document.body.classList.add("pwa-standalone");
    }
    updateOnlineStatus();
    showInstallCard();
    setupFormInterception();
    setupFetchInterception();
    setupPullToRefresh();
    updatePendingIndicator();
    setInterval(updatePendingIndicator, 5000);
  });

  window.addEventListener("load", () => {
    registerServiceWorker().catch((error) => {
      console.warn("PWA registration failed", error);
    });
  });

  const DB_NAME = "SadraBarOutbox";
  const DB_VERSION = 1;
  const STORE_NAME = "requests";

  async function openDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: "id", autoIncrement: true });
          store.createIndex("url", "url", { unique: false });
          store.createIndex("attempts", "attempts", { unique: false });
        }
      };
    });
  }

  async function getPendingCount() {
    try {
      const db = await openDB();
      const tx = db.transaction(STORE_NAME, "readonly");
      const store = tx.objectStore(STORE_NAME);
      const count = await store.count();
      await tx.done;
      await db.close();
      return count;
    } catch (error) {
      console.error("Failed to get pending count", error);
      return 0;
    }
  }

  async function addToOutbox(url, method, headers, body) {
    try {
      const db = await openDB();
      const tx = db.transaction(STORE_NAME, "readwrite");
      const store = tx.objectStore(STORE_NAME);

      await store.add({
        url,
        method,
        headers,
        body,
        attempts: 0,
        createdAt: Date.now(),
        lastAttempt: null
      });

      await tx.done;
      await db.close();

      if (registrationRef && registrationRef.sync) {
        await registrationRef.sync.register("sadrabar-outbox-sync");
      } else {
        scheduleSafariFallbackSync();
      }
    } catch (error) {
      console.error("Failed to add to outbox", error);
    }
  }

  let safariSyncInterval = null;

  function scheduleSafariFallbackSync() {
    if (safariSyncInterval) {
      return;
    }

    const syncNow = async () => {
      const online = await isOnline();
      if (online) {
        try {
          const db = await openDB();
          const tx = db.transaction(STORE_NAME, "readonly");
          const store = tx.objectStore(STORE_NAME);
          const count = await store.count();
          await tx.done;
          await db.close();

          if (count > 0 && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: "SYNC_OUTBOX" });
          }
        } catch (error) {
          console.error("Safari fallback sync failed", error);
        }
      }
    };

    syncNow();
    safariSyncInterval = setInterval(syncNow, 30000);

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) {
        syncNow();
      }
    });

    window.addEventListener("online", syncNow);
  }

  async function isOnline() {
    if (!navigator.onLine) {
      return false;
    }
    try {
      const response = await fetch("/pwa/sync/ping/", { method: "HEAD", cache: "no-store" });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  async function interceptFormSubmit(event) {
    const form = event.target;
    if (!form || form.tagName !== "FORM" || form.hasAttribute("data-no-offline")) {
      return;
    }

    const action = form.action || window.location.href;
    const method = (form.method || "POST").toUpperCase();

    const online = await isOnline();
    if (online) {
      return;
    }

    event.preventDefault();

    const formData = new FormData(form);
    const hasFiles = Array.from(formData.entries()).some(([_, value]) => value instanceof File);
    
    let body;
    let headers = {
      "X-CSRFToken": getCsrfToken()
    };

    if (hasFiles) {
      body = await serializeFormDataWithFiles(formData);
      headers["Content-Type"] = "multipart/form-data; boundary=" + body.boundary;
    } else {
      body = new URLSearchParams(formData).toString();
      headers["Content-Type"] = "application/x-www-form-urlencoded";
    }

    await addToOutbox(action, method, headers, body);
    window.location.href = "/pwa/queued/";
  }

  async function serializeFormDataWithFiles(formData) {
    const boundary = "----WebKitFormBoundary" + Date.now().toString(16);
    const parts = [];

    for (const [name, value] of formData.entries()) {
      if (value instanceof File) {
        const arrayBuffer = await value.arrayBuffer();
        const blob = new Blob([arrayBuffer], { type: value.type });
        parts.push({
          name,
          filename: value.name,
          type: value.type,
          blob
        });
      } else {
        parts.push({
          name,
          value: String(value)
        });
      }
    }

    return { boundary, parts };
  }

  function getCsrfToken() {
    const cookies = document.cookie.split(";");
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split("=");
      if (name === "csrftoken") {
        return decodeURIComponent(value);
      }
    }
    return "";
  }

  function setupFormInterception() {
    document.addEventListener("submit", interceptFormSubmit, true);
  }

  function setupFetchInterception() {
    const originalFetch = window.fetch;
    
    window.fetch = async function(input, init = {}) {
      const url = typeof input === "string" ? input : input.url;
      const method = (init.method || "GET").toUpperCase();
      
      if (method === "GET" || method === "HEAD") {
        return originalFetch(input, init);
      }

      if (init.skipOfflineQueue) {
        return originalFetch(input, init);
      }

      const online = await isOnline();
      if (online) {
        return originalFetch(input, init);
      }

      const headers = init.headers || {};
      let contentType = "";
      
      if (headers instanceof Headers) {
        contentType = headers.get("Content-Type") || "";
      } else {
        contentType = headers["Content-Type"] || headers["content-type"] || "";
      }
      
      let body = init.body;
      let serializedBody;

      if (contentType.includes("application/json") && body) {
        try {
          const jsonData = typeof body === "string" ? JSON.parse(body) : body;
          serializedBody = { isJson: true, data: jsonData };
        } catch (error) {
          serializedBody = body;
        }
      } else if (body instanceof FormData) {
        const hasFiles = Array.from(body.entries()).some(([_, value]) => value instanceof File);
        if (hasFiles) {
          serializedBody = await serializeFormDataWithFiles(body);
        } else {
          serializedBody = new URLSearchParams(body).toString();
        }
      } else {
        serializedBody = body;
      }

      let headersToStore = headers;
      if (headers instanceof Headers) {
        headersToStore = {};
        headers.forEach((value, key) => {
          headersToStore[key] = value;
        });
      }

      await addToOutbox(url, method, headersToStore, serializedBody);
      
      return new Response(JSON.stringify({ 
        queued: true, 
        message: "Request queued for sync" 
      }), { 
        status: 202, 
        headers: { "Content-Type": "application/json" } 
      });
    };
  }

  function setupPullToRefresh() {
    let startY = 0;
    let currentY = 0;
    let isPulling = false;
    let isRefreshing = false;
    const threshold = 80;
    const maxPull = 120;

    const indicator = document.createElement("div");
    indicator.className = "pwa-pull-to-refresh";
    indicator.innerHTML = `
      <span class="pwa-pull-text">برای رفرش بکشید</span>
      <svg class="pwa-pull-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
        <path d="M3 3v5h5"/>
        <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
        <path d="M16 21h5v-5"/>
      </svg>
    `;
    document.body.appendChild(indicator);

    const textEl = indicator.querySelector(".pwa-pull-text");
    const iconEl = indicator.querySelector(".pwa-pull-icon");

    function handleTouchStart(e) {
      if (isRefreshing) return;
      
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      if (scrollTop === 0) {
        startY = e.touches[0].clientY;
        isPulling = true;
      }
    }

    function handleTouchMove(e) {
      if (!isPulling || isRefreshing) return;

      currentY = e.touches[0].clientY;
      const diff = currentY - startY;

      if (diff > 0) {
        e.preventDefault();
        const pullDistance = Math.min(diff * 0.5, maxPull);
        indicator.style.height = `${pullDistance}px`;
        
        const rotation = Math.min((pullDistance / threshold) * 180, 180);
        iconEl.style.transform = `rotate(${rotation}deg)`;

        if (pullDistance >= threshold) {
          textEl.textContent = "رها کنید برای رفرش";
          indicator.classList.add("is-active");
        } else {
          textEl.textContent = "برای رفرش بکشید";
          indicator.classList.remove("is-active");
        }
      }
    }

    function handleTouchEnd() {
      if (!isPulling || isRefreshing) return;
      isPulling = false;

      const pullDistance = parseFloat(indicator.style.height) || 0;

      if (pullDistance >= threshold) {
        triggerRefresh();
      } else {
        resetIndicator();
      }
    }

    function triggerRefresh() {
      isRefreshing = true;
      indicator.classList.add("is-refreshing");
      textEl.textContent = "در حال رفرش...";
      
      setTimeout(() => {
        window.location.reload();
      }, 500);
    }

    function resetIndicator() {
      indicator.style.height = "0";
      indicator.classList.remove("is-active");
      indicator.classList.remove("is-refreshing");
      iconEl.style.transform = "rotate(0deg)";
      textEl.textContent = "برای رفرش بکشید";
    }

    document.addEventListener("touchstart", handleTouchStart, { passive: true });
    document.addEventListener("touchmove", handleTouchMove, { passive: false });
    document.addEventListener("touchend", handleTouchEnd);

    let mouseStartY = 0;
    let isMousePulling = false;

    function handleMouseDown(e) {
      if (isRefreshing) return;
      
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      if (scrollTop === 0 && e.clientY < 50) {
        mouseStartY = e.clientY;
        isMousePulling = true;
      }
    }

    function handleMouseMove(e) {
      if (!isMousePulling || isRefreshing) return;

      const diff = e.clientY - mouseStartY;

      if (diff > 0) {
        const pullDistance = Math.min(diff * 0.5, maxPull);
        indicator.style.height = `${pullDistance}px`;
        
        const rotation = Math.min((pullDistance / threshold) * 180, 180);
        iconEl.style.transform = `rotate(${rotation}deg)`;

        if (pullDistance >= threshold) {
          textEl.textContent = "رها کنید برای رفرش";
          indicator.classList.add("is-active");
        } else {
          textEl.textContent = "برای رفرش بکشید";
          indicator.classList.remove("is-active");
        }
      }
    }

    function handleMouseUp() {
      if (!isMousePulling || isRefreshing) return;
      isMousePulling = false;

      const pullDistance = parseFloat(indicator.style.height) || 0;

      if (pullDistance >= threshold) {
        triggerRefresh();
      } else {
        resetIndicator();
      }
    }

    document.addEventListener("mousedown", handleMouseDown);
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  }

  async function updatePendingIndicator() {
    const count = await getPendingCount();
    let indicator = document.getElementById("pwa-pending-indicator");
    
    if (count > 0) {
      if (!indicator) {
        indicator = document.createElement("div");
        indicator.id = "pwa-pending-indicator";
        indicator.className = "pwa-pending-indicator";
        indicator.innerHTML = `<span>${count}</span>`;
        document.body.appendChild(indicator);
      } else {
        indicator.querySelector("span").textContent = count;
      }
      indicator.classList.add("is-visible");
    } else if (indicator) {
      indicator.classList.remove("is-visible");
    }
  }

  window.SadraBarPWA = {
    install,
    isInstalled: isStandalone,
    requestNotificationPermission,
    sendNotification,
    getRegistration: () => registrationRef,
    showInstall: showInstallCard,
    getPendingCount,
    isOnline,
  };
})();
