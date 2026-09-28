"""Sitemap das publicacoes, para o django.contrib.sitemaps do site.

    from django.contrib.sitemaps.views import sitemap
    from publibot_core.sitemaps import PublicationSitemap

    sitemaps = {"blog": PublicationSitemap, ...as outras paginas do site...}
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}),

`lastmod` e a ultima atualizacao REAL do conteudo; o Google ignora
`priority` e `changefreq`, e por isso eles nao estao aqui.
"""

from __future__ import annotations

from django.contrib.sitemaps import Sitemap

from publibot_core.models import Publication


class PublicationSitemap(Sitemap):
    def items(self):
        return Publication.objects.visiveis().order_by("-created_at")

    def location(self, item):
        return item.get_absolute_url()

    def lastmod(self, item):
        return item.data_de_atualizacao
