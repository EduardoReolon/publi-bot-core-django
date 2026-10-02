"""As rotas assinadas do contrato, em qualquer banco."""

import json
import time
import uuid

import pytest
from django.test import override_settings

from publibot_core.models import Publication, VisitorQuestion
from publibot_core.testing import cabecalhos_assinados

pytestmark = pytest.mark.django_db


def test_health_diz_versao_e_recursos(api):
    resposta = api.get("health/")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["contract_versions"] == ["v1"]
    assert "insights" in dados["capabilities"]


def test_credencial_errada_nonce_repetido_e_relogio_velho_sao_negados(client):
    cabecalhos = cabecalhos_assinados(b"")
    assert client.get("/api/v1/health/", **cabecalhos).status_code == 200
    # Mesmo nonce de novo: reenvio.
    assert client.get("/api/v1/health/", **cabecalhos).status_code == 401

    errada = cabecalhos_assinados(b"", HTTP_X_API_KEY="outra")
    assert client.get("/api/v1/health/", **errada).status_code == 401

    velha = cabecalhos_assinados(b"")
    velha["HTTP_X_TIMESTAMP"] = str(int(time.time()) - 3600)
    assert client.get("/api/v1/health/", **velha).status_code == 401

    adulterada = cabecalhos_assinados(b"")
    adulterada["HTTP_X_SIGNATURE"] = "v1=" + "0" * 64
    assert client.get("/api/v1/health/", **adulterada).status_code == 401


@override_settings(PUBLIBOT_REQUIRE_HTTPS=True)
def test_https_exigido(client):
    assert client.get("/api/v1/health/", **cabecalhos_assinados(b"")).status_code == 403


@override_settings(PUBLIBOT_API_KEY="nova", PUBLIBOT_API_KEY_PREVIOUS="chave-de-teste")
def test_chave_anterior_vale_durante_a_rotacao(client):
    assert (
        client.get(
            "/api/v1/health/", **cabecalhos_assinados(b"", HTTP_X_API_KEY="chave-de-teste")
        ).status_code
        == 200
    )


def test_publicar_e_idempotente_e_sanitiza(api, artigo):
    chave = str(uuid.uuid4())
    primeira = api.post("publish/", artigo, chave=chave)
    assert primeira.status_code == 201
    assert primeira.json()["url"] == "https://exemplo.com.br/blog/como-calcular-o-bdi/"
    segunda = api.post("publish/", artigo, chave=chave)
    assert segunda.status_code == 200 and segunda.json()["status"] == "already_exists"
    assert Publication.objects.count() == 1

    publicacao = Publication.objects.get()
    assert '<aside data-publibot="chamada"></aside>' in publicacao.html_content
    assert publicacao.faq == [{"question": "O que e BDI?", "answer_html": "<p>Uma taxa.</p>"}]
    assert publicacao.call_to_action == "inline"
    assert publicacao.call_to_action_copy == {
        "inline": {"title": "Pagou xcaro?", "text": "Mande a nota.", "button": "Ir"}
    }


def test_script_e_recusado(api, artigo):
    artigo["html_content"] = "<p>oi</p><script>alert(1)</script>"
    assert api.post("publish/", artigo).status_code == 422
    assert not Publication.objects.exists()


def test_atualizar_troca_o_conteudo_e_mantem_o_endereco(api, artigo):
    remote_id = api.post("publish/", artigo).json()["remote_id"]
    artigo["html_content"] = "<p>Versao 2.</p>"
    artigo["slug"] = "outro-endereco"
    chave = str(uuid.uuid4())
    resposta = api.put(f"publications/{remote_id}/", artigo, chave=chave)
    assert resposta.status_code == 200 and resposta.json()["version"] == 2
    de_novo = api.put(f"publications/{remote_id}/", artigo, chave=chave)
    assert de_novo.json()["status"] == "already_applied"
    publicacao = Publication.objects.get()
    assert (
        publicacao.html_content == "<p>Versao 2.</p>" and publicacao.slug == "como-calcular-o-bdi"
    )


def test_seo_context_pagina_sem_pular_nem_repetir(api, artigo):
    for i in range(5):
        artigo["slug"] = f"a-{i}"
        api.post("publish/", artigo)
    vistos, cursor = [], ""
    while True:
        dados = api.get("seo-context/", limit=2, cursor=cursor).json()
        vistos += [p["remote_id"] for p in dados["published_posts"]]
        cursor = dados["next_cursor"]
        if not cursor:
            break
    assert sorted(vistos) == sorted(str(p.pk) for p in Publication.objects.all())
    assert dados["site_title"] == "Site de teste"


def test_reconciliar_pela_chave(api, artigo):
    chave = str(uuid.uuid4())
    api.post("publish/", artigo, chave=chave)
    assert len(api.get("publications/", idempotency_key=chave).json()["results"]) == 1


def test_perguntas_pendentes_e_confirmacao(api):
    perguntas = [VisitorQuestion.objects.create(question_text=f"Pergunta {i}?") for i in range(3)]
    dados = api.get("pending-questions/", limit=2).json()
    assert len(dados["pending_questions"]) == 2 and dados["next_cursor"]
    resto = api.get("pending-questions/", limit=2, cursor=dados["next_cursor"]).json()
    assert len(resto["pending_questions"]) == 1

    ids = [str(perguntas[0].pk), "nao-e-uuid"]
    assert api.post("pending-questions/ack/", {"ids": ids}).json()["acknowledged"] == 1
    assert len(api.get("pending-questions/").json()["pending_questions"]) == 2


def test_resposta_publicada_marca_a_pergunta(api, artigo):
    pergunta = VisitorQuestion.objects.create(question_text="Quanto custa?")
    resposta = dict(artigo, type="qa", question_id=str(pergunta.pk), slug="")
    assert api.post("publish/", resposta).status_code == 201
    pergunta.refresh_from_db()
    assert pergunta.answered_at is not None
    assert pergunta.resposta.kind == "qa"


def test_foto_do_autor_so_quando_falta(api, client, artigo):
    from django.core.files.uploadedfile import SimpleUploadedFile

    referencia = artigo["author"]["reference"]
    artigo["author"]["has_photo"] = True
    assert api.post("publish/", artigo).json()["author_photo_required"] is True

    from django.test.client import encode_multipart

    # Corpo ja montado (e assinado): o test client nao pode remontar.
    fronteira = "FronteiraDoTeste"
    corpo = encode_multipart(
        fronteira,
        {
            "author_reference": referencia,
            "photo": SimpleUploadedFile("a.webp", b"RIFF0000WEBPVP8 ", content_type="image/webp"),
        },
    )
    resposta = client.post(
        "/api/v1/author-photos/",
        corpo,
        content_type=f"multipart/form-data; boundary={fronteira}",
        **cabecalhos_assinados(corpo),
    )
    assert resposta.status_code == 202
    artigo["slug"] = "outro"
    assert api.post("publish/", artigo).json()["author_photo_required"] is False


def test_insights_leva_leitura_e_conversao(api, client, artigo):
    remote_id = api.post("publish/", artigo).json()["remote_id"]
    leitura = {"id": remote_id, "active": 45, "end": True, "cta_seen": True, "cta_click": True}
    client.post("/api/v1/leitura/", json.dumps(leitura), content_type="application/json")
    client.post(
        "/api/v1/conversao/",
        json.dumps(
            {
                "id": str(uuid.uuid4()),
                "kind": "whatsapp",
                "via_cta": True,
                "first_channel": "organic",
                "last_channel": "paid",
                "journey": [{"id": remote_id, "s": 45}, {"id": str(uuid.uuid4()), "s": 3}],
            }
        ),
        content_type="application/json",
    )
    from django.utils import timezone

    dados = api.get("insights/", since=timezone.localdate().isoformat()).json()
    [linha] = dados["reading"]
    assert linha["views"] == 1 and linha["engaged_views"] == 1 and linha["cta_clicks"] == 1
    [conversao] = dados["conversions"]
    assert conversao["last_channel"] == "paid"
    assert conversao["journey"] == [{"remote_id": remote_id, "engaged_seconds": 45}]
