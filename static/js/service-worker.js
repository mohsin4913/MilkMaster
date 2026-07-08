const CACHE_VERSION = "2026-07-08-1";
const SHELL_CACHE = `milkmaster-shell-${CACHE_VERSION}`;
const ASSET_CACHE = `milkmaster-assets-${CACHE_VERSION}`;
const RUNTIME_CACHE = `milkmaster-runtime-${CACHE_VERSION}`;
const CORE_EXTERNAL_ASSETS = [
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
  "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.min.css",
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
];

async function precache(urls, cacheName) {
  const cache = await caches.open(cacheName);
  await cache.addAll(urls);
}

async function getStaticAssetList() {
  const response = await fetch("/pwa-assets.json", { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Unable to load PWA asset list");
  }
  return response.json();
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const assetManifest = await getStaticAssetList();
      await precache(["/", "/offline", "/manifest.json"].concat(assetManifest.shell || []), SHELL_CACHE);
      await precache((assetManifest.assets || []).concat(CORE_EXTERNAL_ASSETS), ASSET_CACHE);
      await self.skipWaiting();
    })()
  );
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => ![SHELL_CACHE, ASSET_CACHE, RUNTIME_CACHE].includes(key))
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  const response = await fetch(request);
  if (response && response.ok) {
    cache.put(request, response.clone());
  }
  return response;
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
  const networkPromise = fetch(request)
    .then((response) => {
      if (response && response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cachedResponse);

  return cachedResponse || networkPromise;
}

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  const { request } = event;
  const url = new URL(request.url);

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const responseClone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, responseClone));
          return response;
        })
        .catch(async () => {
          const cachedPage = await caches.match(request);
          return cachedPage || caches.match("/offline");
        })
    );
    return;
  }

  if (request.destination === "style" || request.destination === "script" || request.destination === "image" || request.destination === "font") {
    if (url.origin === self.location.origin) {
      event.respondWith(cacheFirst(request, ASSET_CACHE));
      return;
    }

    if (url.origin.includes("jsdelivr.net")) {
      event.respondWith(staleWhileRevalidate(request, ASSET_CACHE));
    }
  }
});