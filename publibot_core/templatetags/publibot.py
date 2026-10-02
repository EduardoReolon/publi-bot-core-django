"""Tags para o template do site mostrar a chamada e ligar a medicao.

    {% load publibot %}
    <article data-publibot-id="{{ publicacao.id }}">
      {% corpo_com_chamada publicacao %}
      {% chamada_no_fim publicacao %}
      {% leia_tambem publicacao %}
    </article>

O bloco vem de `publibot/chamada.html`. Sobrescreva esse template no seu
projeto com o texto padrao, o botao e o link da sua oferta. O template recebe
`texto` ({"title", "text", "button"}), escrito pelo PubliBot para o artigo e
para o lugar, ou {} — use-o com o padrao como reserva.
"""

from __future__ import annotations

import json

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from publibot_core import conf

register = template.Library()


def _bloco(publicacao, onde: str) -> str:
    contexto = {"publicacao": publicacao, "onde": onde, "texto": publicacao.texto_da_chamada(onde)}
    return render_to_string("publibot/chamada.html", contexto)


@register.simple_tag
def corpo_com_chamada(publicacao):
    """O corpo, com o bloco no lugar da marca quando o artigo pede (inline)."""
    # O html_content ja foi sanitizado ao ser recebido.
    return mark_safe(publicacao.html_com_chamada(_bloco(publicacao, "meio")))


@register.inclusion_tag("publibot/relacionados.html")
def leia_tambem(publicacao):
    """Os links internos escolhidos pelo PubliBot, se houver."""
    return {"relacionados": publicacao.related_articles or []}


_ESCAPE_DO_JSON = {ord(">"): "\\u003E", ord("<"): "\\u003C", ord("&"): "\\u0026"}


def _json_ld(dados: dict) -> str:
    """Um bloco JSON-LD, escapado para nao fechar o <script> antes da hora."""
    texto = json.dumps(dados, ensure_ascii=False).translate(_ESCAPE_DO_JSON)
    return f'<script type="application/ld+json">{texto}</script>'


def dados_estruturados(publicacao) -> list[dict]:
    """Article (e FAQPage, se houver perguntas) no formato do schema.org."""
    artigo = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": publicacao.title,
        "description": publicacao.meta_description or publicacao.excerpt,
        "mainEntityOfPage": publicacao.url,
        "datePublished": publicacao.data_de_publicacao.isoformat(),
        "dateModified": publicacao.data_de_atualizacao.isoformat(),
        "inLanguage": publicacao.language,
    }
    if publicacao.author_name:
        autor = {"@type": "Person", "name": publicacao.author_name}
        if publicacao.author_credentials:
            autor["description"] = publicacao.author_credentials
        artigo["author"] = autor
    capa = publicacao.capa_url
    if capa:
        artigo["image"] = capa if capa.startswith("http") else _absoluta(capa)
    titulo_do_site = conf.texto("PUBLIBOT_SITE_TITLE")
    if titulo_do_site:
        artigo["publisher"] = {"@type": "Organization", "name": titulo_do_site}
    blocos = [artigo]
    if publicacao.faq:
        blocos.append(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["answer_html"]},
                    }
                    for item in publicacao.faq
                ],
            }
        )
    return blocos


def _absoluta(caminho: str) -> str:
    return conf.valor("PUBLIBOT_PUBLIC_URL").rstrip("/") + caminho


@register.simple_tag
def publibot_head(publicacao):
    """O que vai no <head> da pagina do artigo: title, description, canonical,
    Open Graph e JSON-LD. Ver docs/SEO_DO_SITE.md."""
    capa = publicacao.capa_url
    if capa and not capa.startswith("http"):
        capa = _absoluta(capa)
    contexto = {
        "p": publicacao,
        "capa": capa,
        "site": conf.texto("PUBLIBOT_SITE_TITLE"),
        "json_ld": mark_safe("".join(_json_ld(b) for b in dados_estruturados(publicacao))),
    }
    return render_to_string("publibot/head.html", contexto)


@register.simple_tag
def foto_do_autor(publicacao):
    """A URL da foto do autor, ou "" (a foto chega depois da publicacao)."""
    foto = publicacao.foto_do_autor
    return foto.image.url if foto and foto.image else ""


@register.simple_tag
def chamada_no_fim(publicacao):
    """O bloco no fim, para `end` e `inline`; nada para `none`."""
    if not publicacao.chamada_no_fim:
        return ""
    return mark_safe(_bloco(publicacao, "fim"))
