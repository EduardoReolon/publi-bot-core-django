from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from publibot_core.sitemaps import PublicationSitemap

urlpatterns = [
    path("api/v1/", include("publibot_core.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": {"blog": PublicationSitemap}}),
]
