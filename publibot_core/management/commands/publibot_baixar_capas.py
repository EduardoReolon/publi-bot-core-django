"""Baixa as capas que ainda nao estao no site (rede fora, digest errado).

    python manage.py publibot_baixar_capas

Pode ir num cron de hora em hora; sem pendencia, nao faz nada.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from publibot_core.capa import baixar, pendentes


class Command(BaseCommand):
    help = "Baixa as capas pendentes das publicacoes do PubliBot."

    def handle(self, *args, **options):
        total = ok = 0
        for publicacao in pendentes():
            total += 1
            ok += baixar(publicacao)
        self.stdout.write(f"{ok} de {total} capa(s) baixada(s).")
