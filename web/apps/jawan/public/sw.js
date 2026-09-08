/* SAARTHI jawan app service worker — app-shell offline support (ADR-0005).
   Data offline-ness lives in IndexedDB (packages/sync); this SW only keeps
   the shell loadable without a network. API calls are never cached. */

const CACHE = "saarthi-shell-v2";
const SHELL = ["/", "/roster", "/manifest.webmanifest", "/icons/icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET") return;

  // Static assets: cache-first, populate on the way past.
  if (url.pathname.startsWith("/_next/static/") || url.pathname.startsWith("/icons/")) {
    event.respondWith(
      caches.match(event.request).then(
        (hit) =>
          hit ||
          fetch(event.request).then((res) => {
            const clone = res.clone();
            caches.open(CACHE).then((c) => c.put(event.request, clone));
            return res;
          }),
      ),
    );
    return;
  }

  // Navigations: network-first, cached shell as fallback. Always respond —
  // an undefined response would surface as a hard network error offline.
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          const clone = res.clone();
          caches.open(CACHE).then((c) => c.put("/", clone));
          return res;
        })
        .catch(async () => {
          const cached = await caches.match("/");
          if (cached) return cached;
          return new Response(
            "<!doctype html><html><body><h1>SAARTHI</h1><p>Offline — open once with a connection to load the app.</p></body></html>",
            { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } },
          );
        }),
    );
  }
});
