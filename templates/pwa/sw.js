const PWA_VERSION = "{{ version|escapejs }}";
const STATIC_CACHE = `sadrabar-static-${PWA_VERSION}`;
const PAGE_CACHE = `sadrabar-pages-${PWA_VERSION}`;
const OFFLINE_URL = "{{ offline_url|escapejs }}";
const APP_SHELL = [
  OFFLINE_URL{% for url in static_urls %},
  "{{ url|escapejs }}"{% endfor %}
];
const STATIC_EXTENSIONS = [
  ".css",
  ".js",
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
  ".gif",
  ".svg",
  ".ico",
  ".woff",
  ".woff2",
  ".ttf"
];
const BYPASS_PATHS = [
  "/admin/",
  "/accounts/logout/",
  "/contact/submit/"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => (
      cache.addAll(APP_SHELL).catch((error) => {
        console.warn("PWA shell cache skipped some assets", error);
      })
    ))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys
        .filter((key) => key.startsWith("sadrabar-") && ![STATIC_CACHE, PAGE_CACHE].includes(key))
        .map((key) => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("fetch", (event) => {
  const request = event.request;

  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);
  if (url.origin !== self.location.origin || BYPASS_PATHS.some((path) => url.pathname.startsWith(path))) {
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(networkFirstPage(request));
    return;
  }

  if (url.pathname.startsWith("/static/") || STATIC_EXTENSIONS.some((ext) => url.pathname.endsWith(ext))) {
    event.respondWith(cacheFirst(request));
  }
});

async function networkFirstPage(request) {
  const cache = await caches.open(PAGE_CACHE);
  try {
    const response = await fetch(request);
    if (isCacheable(response)) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    return cached || caches.match(OFFLINE_URL);
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    refreshCache(request);
    return cached;
  }

  const response = await fetch(request);
  if (isCacheable(response)) {
    const cache = await caches.open(STATIC_CACHE);
    cache.put(request, response.clone());
  }
  return response;
}

async function refreshCache(request) {
  try {
    const response = await fetch(request);
    if (isCacheable(response)) {
      const cache = await caches.open(STATIC_CACHE);
      await cache.put(request, response);
    }
  } catch (error) {
    {% if debug %}console.debug("PWA refresh failed", request.url, error);{% endif %}
  }
}

function isCacheable(response) {
  return response && response.status === 200 && ["basic", "default"].includes(response.type);
}

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (error) {
    data = { body: event.data ? event.data.text() : "" };
  }

  const title = data.title || "صدرابار";
  const options = {
    body: data.body || "پیام جدید از سامانه صدرابار",
    icon: "/static/pwa/icons/icon-192x192.png",
    badge: "/static/pwa/icons/icon-72x72.png",
    dir: "rtl",
    lang: "fa-IR",
    data: { url: data.url || "/" },
    tag: data.tag || "sadrabar-notification",
    renotify: Boolean(data.renotify),
    vibrate: [120, 70, 120],
    actions: [
      { action: "open", title: "باز کردن" },
      { action: "dismiss", title: "بستن" }
    ]
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  if (event.action === "dismiss") {
    return;
  }

  const targetUrl = new URL(event.notification.data && event.notification.data.url ? event.notification.data.url : "/", self.location.origin).href;
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url === targetUrl && "focus" in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
      return undefined;
    })
  );
});
