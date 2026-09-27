"""Tabelas da propria biblioteca. O site nao le nem grava nelas.

Ficam fora de `publibot_core.models.__all__`: quem monta o site so precisa de
Publication, VisitorQuestion e AuthorPhoto.
"""

from __future__ import annotations

from django.db import models
from django.utils import timezone


class DailyReading(models.Model):
    """Leitura de uma publicacao num dia: so contadores, nenhum leitor.

    Alimentada pelo leitura.js (rota publica leitura/) e lida pelo PubliBot
    (rota assinada insights/).
    """

    publication = models.ForeignKey(
        "publibot_core.Publication", on_delete=models.CASCADE, related_name="+"
    )
    day = models.DateField()
    views = models.PositiveIntegerField(default=0)
    engaged_views = models.PositiveIntegerField(default=0)
    engaged_seconds = models.PositiveIntegerField(default=0)
    read_to_end = models.PositiveIntegerField(default=0)
    cta_views = models.PositiveIntegerField(default=0)
    cta_clicks = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["publication", "day"], name="publibot_leitura_do_dia")
        ]


class Conversion(models.Model):
    """Uma conversao e os artigos lidos antes dela. O id vem do navegador:
    reenviar nao duplica."""

    id = models.UUIDField(primary_key=True)
    day = models.DateField(db_index=True)
    kind = models.CharField(max_length=40, blank=True)
    via_cta = models.BooleanField(default=False)
    # "paid", "organic", "social", "referral", "email", "direct" ou "other".
    first_channel = models.CharField(max_length=10, blank=True)
    last_channel = models.CharField(max_length=10, blank=True)
    journey = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class UsedNonce(models.Model):
    """Nonce ja aceito numa requisicao assinada, contra reenvio.

    No banco, e nao no cache: com cache em memoria e varios processos (o caso
    comum com gunicorn), cada processo teria a sua lista e o mesmo pedido
    passaria uma vez em cada. O indice UNICO decide ate entre requisicoes
    simultaneas.
    """

    nonce = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
