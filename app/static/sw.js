/**
 * ResearchDose — Progressive Web App (PWA) Service Worker
 * Supports offline dose conversion, cache-first static shell, and background sync.
 */

const CACHE_NAME = "researchdose-v1.0.0";

// Core static assets to precache immediately
const PRECACHE_ASSETS = [
    "/",
    "/manifest.json",
    "/static/css/main.css",
    "/static/js/main.js",
    "/static/manifest.json",
    "/static/icons/icon.svg",
    "/static/icons/icon-192x192.png",
    "/static/icons/icon-512x512.png",
    "/static/icons/icon-maskable-512x512.png",
    "/static/icons/apple-touch-icon.png",
    "/static/icons/favicon.ico",
    "/static/icons/favicon-32x32.png",
    "/api/species",
    "/api/references",
    // Essential CDN Assets
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
];

// Install Event: Pre-cache static assets
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(async (cache) => {
            console.log("[ServiceWorker] Pre-caching offline application shell");
            // Cache core assets gracefully (don't fail install if a non-critical CDN asset times out)
            const cachePromises = PRECACHE_ASSETS.map(async (url) => {
                try {
                    const response = await fetch(url, { mode: "cors" });
                    if (response.ok || response.type === "opaque") {
                        await cache.put(url, response);
                    }
                } catch (err) {
                    console.warn("[ServiceWorker] Asset failed to precache (will fetch on demand):", url, err);
                }
            });
            await Promise.all(cachePromises);
        })
    );
    self.skipWaiting();
});

// Activate Event: Clean up legacy caches
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    if (name !== CACHE_NAME) {
                        console.log("[ServiceWorker] Removing obsolete cache:", name);
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch Event Strategy
self.addEventListener("fetch", (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests (e.g. POST /api/calculate handled with offline client fallback in main.js)
    if (request.method !== "GET") {
        return;
    }

    // 1. Navigation requests (HTML Pages): Network-First, fallback to Cache
    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put("/", responseClone));
                    }
                    return networkResponse;
                })
                .catch(async () => {
                    console.log("[ServiceWorker] Serving cached application page for navigation offline");
                    const cachedResponse = await caches.match("/") || await caches.match(request);
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    return new Response(
                        `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>ResearchDose — Offline</title><style>body{background:#0a0f1d;color:#fff;font-family:sans-serif;text-align:center;padding:40px;}</style></head><body><h2>ResearchDose is in Offline Mode</h2><p>Please open the app from your home screen or refresh once connected.</p></body></html>`,
                        { headers: { "Content-Type": "text/html" } }
                    );
                })
        );
        return;
    }

    // 2. Static Assets (CSS, JS, Fonts, Icons, Images): Stale-While-Revalidate
    if (
        url.pathname.startsWith("/static/") ||
        url.hostname.includes("cdn.jsdelivr.net") ||
        url.hostname.includes("fonts.googleapis.com") ||
        url.hostname.includes("fonts.gstatic.com")
    ) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                const fetchPromise = fetch(request)
                    .then((networkResponse) => {
                        if (networkResponse && (networkResponse.status === 200 || networkResponse.type === "opaque")) {
                            const responseClone = networkResponse.clone();
                            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
                        }
                        return networkResponse;
                    })
                    .catch(() => cachedResponse);

                return cachedResponse || fetchPromise;
            })
        );
        return;
    }

    // 3. API Read Requests (/api/species, /api/references): Network-First with Cache fallback
    if (url.pathname.startsWith("/api/")) {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
                    }
                    return networkResponse;
                })
                .catch(() => caches.match(request))
        );
        return;
    }

    // Default strategy: Stale-While-Revalidate
    event.respondWith(
        caches.match(request).then((cachedResponse) => {
            return (
                cachedResponse ||
                fetch(request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
                    }
                    return networkResponse;
                })
            );
        })
    );
});
