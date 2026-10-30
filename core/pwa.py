"""
Progressive Web App (PWA) + Android app support.

  /manifest.json                 → app name, icons, colors (used by Chrome "Install app" & PWABuilder)
  /sw.js                         → service worker (offline page + faster loading)
  /offline/                      → page shown when there is no internet
  /.well-known/assetlinks.json   → proves the Android app (TWA) belongs to this website
"""
import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.utils.translation import get_language
from django.views.decorators.cache import cache_control

from .models import SiteSetting, ThemeSetting


@cache_control(max_age=3600)
def manifest(request):
    site = SiteSetting.load()
    theme = ThemeSetting.load()
    data = {
        "id": "/",
        "name": site.site_name,
        "short_name": site.site_name[:12],
        "description": site.tagline,
        "lang": get_language() or "en",
        "start_url": "/?source=app",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": theme.page_bg,
        "theme_color": theme.header_bg,
        "categories": ["shopping"],
        "icons": [
            {"src": static("img/icons/icon-192.png"), "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": static("img/icons/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": static("img/icons/maskable-512.png"), "sizes": "512x512", "type": "image/png",
             "purpose": "maskable"},
        ],
        "shortcuts": [
            {"name": "Cart", "url": "/cart/", "icons": [{"src": static("img/icons/icon-192.png"), "sizes": "192x192"}]},
            {"name": "My Orders", "url": "/orders/my/",
             "icons": [{"src": static("img/icons/icon-192.png"), "sizes": "192x192"}]},
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json")


SW_TEMPLATE = r"""
// ShopBD service worker — version __VERSION__
const CACHE = "shopbd-__VERSION__";
const OFFLINE_URL = "/offline/";
const PRECACHE = [OFFLINE_URL, "__CSS__", "__JS__", "__ICON__"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Pages: always try the network first (prices & stock must be fresh), offline page if no internet
  if (req.mode === "navigate") {
    event.respondWith(fetch(req).catch(() => caches.match(OFFLINE_URL)));
    return;
  }
  // Static files & product images: serve from cache, update in background
  if (url.origin === location.origin && (url.pathname.startsWith("/static/") || url.pathname.startsWith("/media/"))) {
    event.respondWith(
      caches.open(CACHE).then((cache) =>
        cache.match(req).then((hit) => {
          const net = fetch(req).then((res) => { if (res.ok) cache.put(req, res.clone()); return res; }).catch(() => hit);
          return hit || net;
        })
      )
    );
  }
});
"""


def service_worker(request):
    js = (SW_TEMPLATE
          .replace("__VERSION__", getattr(settings, "APP_VERSION", "1"))
          .replace("__CSS__", static("css/style.css"))
          .replace("__JS__", static("js/main.js"))
          .replace("__ICON__", static("img/icons/icon-192.png")))
    response = HttpResponse(js, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


def offline(request):
    return render(request, "core/offline.html")


def assetlinks(request):
    """Digital Asset Links for the Android app (only needed for the Trusted Web Activity / PWABuilder app)."""
    package = getattr(settings, "ANDROID_PACKAGE_NAME", "")
    fingerprints = getattr(settings, "ANDROID_SHA256_FINGERPRINTS", [])
    data = []
    if package and fingerprints:
        data = [{
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {"namespace": "android_app", "package_name": package,
                       "sha256_cert_fingerprints": fingerprints},
        }]
    return HttpResponse(json.dumps(data, indent=2), content_type="application/json")
