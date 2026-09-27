"""O que o template do site usa."""

import datetime
import uuid

import pytest
from django.core.management import call_command
from django.template import Context, Template
from django.utils import timezone

from publibot_core.models import Publication

pytestmark = pytest.mark.django_db


def _publicacao(**campos):
    padrao = {
        "idempotency_key": uuid.uuid4(),
        "kind": "article",
        "title": "T",
        "slug": "t",
        "html_content": '<p>a</p><aside data-publibot="chamada"></aside><p>b</p>',
        "call_to_action": "inline",
    }
    return Publication.objects.create(**{**padrao, **campos})


def test_visiveis_respeita_status_e_agendamento():
    agora = timezone.now()
    ok = _publicacao()
    _publicacao(post_status="draft")
    _publicacao(post_status="scheduled", publish_at=agora + datetime.timedelta(days=1))
    passou = _publicacao(post_status="scheduled", publish_at=agora - datetime.timedelta(hours=1))
    assert set(Publication.objects.visiveis()) == {ok, passou}


def test_tags_da_chamada_leia_tambem_e_foto():
    p = _publicacao(related_articles=[{"title": "Outro", "url": "https://x.com/o/"}])
    html = Template(
        "{% load publibot %}{% corpo_com_chamada p %}|{% chamada_no_fim p %}|"
        "{% leia_tambem p %}|{% foto_do_autor p %}"
    ).render(Context({"p": p}))
    meio, fim, relacionados, foto = html.split("|")
    assert "publibot-chamada--meio" in meio and "data-publibot" not in meio.split("<aside")[0]
    assert "publibot-chamada--fim" in fim
    assert "https://x.com/o/" in relacionados
    assert foto == ""

    sem = _publicacao(call_to_action="none")
    html = Template("{% load publibot %}{% corpo_com_chamada p %}{% chamada_no_fim p %}").render(
        Context({"p": sem})
    )
    assert "aside" not in html


def test_url_segue_o_settings(settings):
    settings.PUBLIBOT_ARTICLE_PATH = "/artigos/{slug}/"
    assert _publicacao(slug="bdi").url == "https://exemplo.com.br/artigos/bdi/"


def test_comando_de_conferencia(capsys, settings):
    settings.PUBLIBOT_REQUIRE_HTTPS = True
    call_command("publibot_conferir")
    assert "Pronto para receber" in capsys.readouterr().out
