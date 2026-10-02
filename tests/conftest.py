import json
import uuid

import pytest
from django.core.cache import cache

from publibot_core.testing import cabecalhos_assinados


@pytest.fixture(autouse=True)
def _cache_limpo():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api(client):
    """Chama as rotas assinadas como o PubliBot chamaria."""

    class Api:
        def get(self, rota, **params):
            return client.get(f"/api/v1/{rota}", params, **cabecalhos_assinados(b""))

        def post(self, rota, dados, *, chave=None):
            corpo = json.dumps(dados).encode()
            return client.post(
                f"/api/v1/{rota}",
                corpo,
                content_type="application/json",
                **cabecalhos_assinados(corpo, idempotency_key=chave or str(uuid.uuid4())),
            )

        def put(self, rota, dados, *, chave):
            corpo = json.dumps(dados).encode()
            return client.put(
                f"/api/v1/{rota}",
                corpo,
                content_type="application/json",
                **cabecalhos_assinados(corpo, idempotency_key=chave),
            )

    return Api()


ARTIGO = {
    "type": "article",
    "title": "Como calcular o BDI",
    "slug": "como-calcular-o-bdi",
    "html_content": (
        "<p>Texto <a href='https://tcu.gov.br/x'>fonte</a>.</p>"
        '<aside data-publibot="chamada"></aside><p>Fim.</p>'
    ),
    "excerpt": "Resumo.",
    "meta_description": "Meta.",
    "focus_keyword": "bdi",
    "status": "published",
    "author": {"name": "Ana", "credentials": "CREA", "reference": str(uuid.uuid4())},
    "faq": [{"question": "O que e BDI?", "answer_html": "<p>Uma taxa.</p>"}],
    "call_to_action": "inline",
    "call_to_action_copy": {
        "inline": {
            "title": "Pagou <script>x</script>caro?",
            "text": "Mande  a\nnota.",
            "button": "Ir",
        },
        "end": {"title": "So titulo"},
    },
    "related_articles": [{"remote_id": "1", "title": "Outro", "url": "https://exemplo.com.br/b/"}],
}


@pytest.fixture
def artigo():
    return json.loads(json.dumps(ARTIGO))
