from __future__ import annotations

from django.apps import AppConfig


class PublibotCoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "publibot_core"
    verbose_name = "PubliBot"
