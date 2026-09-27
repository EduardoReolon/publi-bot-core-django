"""Configuracoes da biblioteca, lidas do settings.py do site.

Todas comecam com PUBLIBOT_. So as duas credenciais sao obrigatorias; o resto
tem padrao. Lidas a cada uso (e nao na importacao), para que override_settings
e mudancas em tempo de teste funcionem.
"""

from __future__ import annotations

from django.conf import settings
from django.utils.module_loading import import_string

PADROES = {
    # Credenciais (obrigatorias). Geradas no cadastro do site no PubliBot.
    "PUBLIBOT_API_KEY": "",
    "PUBLIBOT_SIGNING_SECRET": "",
    # Durante uma rotacao de chave, a anterior continua aceita.
    "PUBLIBOT_API_KEY_PREVIOUS": "",
    # Endereco publico do site, sem barra no fim: https://www.exemplo.com.br
    "PUBLIBOT_PUBLIC_URL": "",
    # Caminho de cada tipo de conteudo. {slug}, {id} e {question_id} sao trocados.
    "PUBLIBOT_ARTICLE_PATH": "/blog/{slug}/",
    "PUBLIBOT_QA_PATH": "/perguntas/{question_id}/",
    # O que o PubliBot le para entender o site (rota seo-context). Texto, ou o
    # caminho de uma funcao sem argumentos que devolve o texto.
    "PUBLIBOT_SITE_TITLE": "",
    "PUBLIBOT_HOME_TEXT": "",
    # None = exige HTTPS fora do DEBUG. True/False forca.
    "PUBLIBOT_REQUIRE_HTTPS": None,
}


def valor(nome: str):
    return getattr(settings, nome, PADROES[nome])


def texto(nome: str) -> str:
    """Um texto do settings, ou o que a funcao apontada por ele devolve."""
    bruto = valor(nome) or ""
    if isinstance(bruto, str) and bruto.startswith("func:"):
        return str(import_string(bruto.removeprefix("func:"))() or "")
    if callable(bruto):
        return str(bruto() or "")
    return str(bruto)


def exige_https() -> bool:
    forcado = valor("PUBLIBOT_REQUIRE_HTTPS")
    if forcado is None:
        return not settings.DEBUG
    return bool(forcado)
