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
  });

  window.addEventListener("load", () => {
    registerServiceWorker().catch((error) => {
      console.warn("PWA registration failed", error);
    });
  });

  window.SadraBarPWA = {
    install,
    isInstalled: isStandalone,
    requestNotificationPermission,
    sendNotification,
    getRegistration: () => registrationRef,
    showInstall: showInstallCard,
  };
})();
