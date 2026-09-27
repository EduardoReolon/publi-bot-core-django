"""Confere a instalacao no site: settings, migracoes, midia e HTTPS.

    python manage.py publibot_conferir

A ponta de la (o PubliBot conseguir falar com este site) se confere no
PubliBot: manage.py conferir_instalacao, linha "site".
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import NoReverseMatch, reverse

from publibot_core import conf


class Command(BaseCommand):
    help = "Confere se o publibot_core esta pronto para receber conteudo."

    def handle(self, *args, **options):
        falhas = 0

        def linha(ok: bool, texto: str) -> None:
            nonlocal falhas
            falhas += not ok
            marca = self.style.SUCCESS("OK   ") if ok else self.style.ERROR("FALHA")
            self.stdout.write(f"  {marca} {texto}")

        for nome in ("PUBLIBOT_API_KEY", "PUBLIBOT_SIGNING_SECRET", "PUBLIBOT_PUBLIC_URL"):
            linha(bool(conf.valor(nome)), f"{nome} {'definida' if conf.valor(nome) else 'vazia'}")

        executor = MigrationExecutor(connection)
        pendentes = [
            m
            for m, _ in executor.migration_plan(executor.loader.graph.leaf_nodes())
            if m.app_label == "publibot_core"
        ]
        linha(not pendentes, "migracoes em dia" if not pendentes else "rode: manage.py migrate")

        try:
            rota = reverse("publibot_core:health")
            linha(True, f"rotas publicadas em {rota.removesuffix('health/')}")
        except NoReverseMatch:
            linha(False, 'inclua path("api/v1/", include("publibot_core.urls")) no urls.py')

        try:
            raiz = Path(settings.MEDIA_ROOT)
            raiz.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=raiz, delete=True):
                pass
            linha(True, f"MEDIA_ROOT grava ({raiz}) — fotos de autor")
        except (OSError, TypeError) as exc:
            linha(False, f"MEDIA_ROOT nao grava: {exc}")

        limite = getattr(settings, "DATA_UPLOAD_MAX_MEMORY_SIZE", 2_621_440) or 0
        linha(
            limite == 0 or limite >= 6 * 1024 * 1024,
            f"DATA_UPLOAD_MAX_MEMORY_SIZE = {limite} (fotos de autor pedem >= 6 MB)",
        )
        linha(conf.exige_https(), "HTTPS exigido nas rotas (fora do DEBUG)")

        if falhas:
            self.stdout.write(self.style.ERROR(f"{falhas} item(ns) a corrigir."))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("Pronto para receber conteudo do PubliBot."))
