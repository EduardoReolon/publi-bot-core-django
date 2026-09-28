"""O <head> de SEO, o sitemap e a capa baixada para o site."""

import hashlib
import io
import json
import re
import uuid

import pytest
from django.template import Context, Template

from publibot_core import capa
from publibot_core.models import Publication

pytestmark = pytest.mark.django_db


def _publicacao(**campos):
    padrao = {
        "idempotency_key": uuid.uuid4(),
        "kind": "article",
        "title": "Como calcular o BDI",
        "slug": "bdi",
        "html_content": "<p>a</p>",
        "meta_description": "O que entra no BDI </script> e como calcular.",
        "author_name": "Ana",
        "author_credentials": "CREA 123",
        "canonical_source": "https://tcu.gov.br/estudo",
        "faq": [{"question": "O que e?", "answer_html": "<p>Uma taxa.</p>"}],
    }
    return Publication.objects.create(**{**padrao, **campos})


def test_head_tem_canonical_proprio_og_e_json_ld():
    p = _publicacao()
    html = Template("{% load publibot %}{% publibot_head p %}").render(Context({"p": p}))
    # O canonical e o proprio artigo, NUNCA a fonte citada.
    assert '<link rel="canonical" href="https://exemplo.com.br/blog/bdi/">' in html
    assert "tcu.gov.br" not in html
    assert 'property="og:title"' in html
    blocos = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    artigo, faq = (json.loads(b) for b in blocos)
    assert artigo["@type"] == "Article" and artigo["author"]["name"] == "Ana"
    assert artigo["mainEntityOfPage"] == "https://exemplo.com.br/blog/bdi/"
    assert faq["@type"] == "FAQPage"
    # Texto do conteudo nao fecha o <script> antes da hora.
    assert "</script> e como" not in blocos[0]


def test_sitemap_so_com_o_que_esta_no_ar(client):
    _publicacao()
    _publicacao(slug="rascunho", post_status="draft")
    xml = client.get("/sitemap.xml").content.decode()
    assert "/blog/bdi/" in xml and "rascunho" not in xml and "<lastmod>" in xml


def test_capa_baixada_confere_o_digest(monkeypatch):
    conteudo = b"RIFF1234WEBPVP8 imagem"
    p = _publicacao(
        cover_image_url="https://publibot.exemplo/capas/x.webp",
        cover_image_sha256=hashlib.sha256(conteudo).hexdigest(),
    )
    monkeypatch.setattr(capa.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(conteudo))
    assert p.capa_url == "https://publibot.exemplo/capas/x.webp"  # antes de baixar
    assert capa.baixar(p)
    p.refresh_from_db()
    assert p.capa_url.startswith("/media/publibot/capas/")

    outra = _publicacao(
        slug="b", cover_image_url="https://publibot.exemplo/y.webp", cover_image_sha256="0" * 64
    )
    assert not capa.baixar(outra)  # digest nao confere: nao grava
    assert list(capa.pendentes()) == [outra]


def test_publicar_agenda_a_capa(api, artigo, monkeypatch):
    agendadas = []
    monkeypatch.setattr("publibot_core.views.agendar_download_da_capa", agendadas.append)
    artigo["cover_image"] = {"url": "https://publibot.exemplo/c.webp", "sha256": "a" * 64}
    api.post("publish/", artigo)
    [publicacao] = agendadas
    assert publicacao.cover_image_sha256 == "a" * 64
