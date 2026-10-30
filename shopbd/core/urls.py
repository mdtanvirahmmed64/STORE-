from django.urls import path

from . import pwa, views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("page/<slug:slug>/", views.page_detail, name="page"),
    path("contact/", views.contact, name="contact"),
    path("subscribe/", views.subscribe, name="subscribe"),
    path("dashboard/", views.staff_dashboard, name="staff_dashboard"),
    # App / PWA
    path("manifest.json", pwa.manifest, name="manifest"),
    path("sw.js", pwa.service_worker, name="service_worker"),
    path("offline/", pwa.offline, name="offline"),
    path(".well-known/assetlinks.json", pwa.assetlinks, name="assetlinks"),
]
