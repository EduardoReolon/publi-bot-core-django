"""Baixar a capa do artigo para o site (o contrato pede: sem hotlink).

A URL aponta para o PubliBot. O download roda numa thread depois da resposta,
para a publicacao nao esperar pela imagem (o PubliBot tem tempo limite de
leitura). O que falhar (rede, digest) fica para o comando
`manage.py publibot_baixar_capas`, que pode ir num cron.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import urllib.request

from django.core.files.base import ContentFile
from django.db import close_old_connections, transaction

logger = logging.getLogger("publibot_core")

TAMANHO_MAXIMO = 10 * 1024 * 1024
TEMPO_LIMITE = 20


def pendentes():
    """Publicacoes com capa informada que o site ainda nao guardou."""
    from publibot_core.models import Publication

    return Publication.objects.exclude(cover_image_url="").filter(cover_image="")


def baixar(publicacao) -> bool:
    """Baixa, confere o sha256 e grava. True se a capa ficou no site."""
    url = publicacao.cover_image_url
    if not url.startswith("https://") and not url.startswith("http://"):
        return False
    try:
        pedido = urllib.request.Request(url, headers={"User-Agent": "publi-bot-core-django"})
        with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE) as resposta:
            conteudo = resposta.read(TAMANHO_MAXIMO + 1)
    except OSError as exc:
        logger.warning("Capa de %s nao baixou: %s", publicacao.pk, exc)
        return False
    if len(conteudo) > TAMANHO_MAXIMO:
        logger.warning("Capa de %s acima do limite.", publicacao.pk)
        return False
    digest = hashlib.sha256(conteudo).hexdigest()
    if publicacao.cover_image_sha256 and digest != publicacao.cover_image_sha256:
        logger.warning("Capa de %s com digest diferente do informado.", publicacao.pk)
        return False
    publicacao.cover_image.save(f"{publicacao.pk}-{digest[:12]}.webp", ContentFile(conteudo))
    return True


def _em_segundo_plano(pk) -> None:
    from publibot_core.models import Publication

    close_old_connections()
    try:
        publicacao = Publication.objects.filter(pk=pk).first()
        if publicacao is not None:
            baixar(publicacao)
    finally:
        close_old_connections()


def agendar_download_da_capa(publicacao) -> None:
    """Depois do commit, baixa a capa numa thread, se for nova ou trocou."""
    if not publicacao.cover_image_url:
        return
    if publicacao.cover_image and publicacao.cover_image.name.endswith(
        f"{publicacao.cover_image_sha256[:12]}.webp"
    ):
        return  # a mesma capa ja esta no site
    if publicacao.cover_image:
        publicacao.cover_image = ""
        publicacao.save(update_fields=["cover_image"])
    pk = publicacao.pk
    transaction.on_commit(
        lambda: threading.Thread(target=_em_segundo_plano, args=(pk,), daemon=True).start()
    )
