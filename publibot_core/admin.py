"""No admin, so o que interessa a quem cuida do site."""

from __future__ import annotations

from django.contrib import admin

from publibot_core.models import AuthorPhoto, Publication, VisitorQuestion


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    """Somente leitura: o conteudo e do PubliBot. Corrigir aqui seria
    sobrescrito na proxima atualizacao; corrija la e reenvie."""

    list_display = ["title", "kind", "post_status", "published_at", "version"]
    list_filter = ["kind", "post_status"]
    search_fields = ["title", "slug"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(VisitorQuestion)
class VisitorQuestionAdmin(admin.ModelAdmin):
    list_display = ["question_text", "submitted_at", "acknowledged_at", "answered_at"]
    list_filter = ["answered_at"]


@admin.register(AuthorPhoto)
class AuthorPhotoAdmin(admin.ModelAdmin):
    list_display = ["author_reference", "received_at"]

    def has_add_permission(self, request):
        return False
