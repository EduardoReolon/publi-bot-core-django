"""As tabelas que o site le (e, no caso das perguntas, grava)."""

from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class PublicationQuerySet(models.QuerySet):
    def visiveis(self):
        """Artigos publicados, cuja data de publicacao ja chegou. O que a lista
        do blog e a pagina do artigo devem mostrar."""
        agora = timezone.now()
        return self.filter(
            kind=Publication.Kind.ARTICLE,
            post_status__in=[Publication.Status.PUBLISHED, Publication.Status.SCHEDULED],
        ).filter(models.Q(publish_at__isnull=True) | models.Q(publish_at__lte=agora))

    def respostas_visiveis(self):
        """Respostas a perguntas de visitantes, publicadas."""
        return self.filter(kind=Publication.Kind.QA, post_status=Publication.Status.PUBLISHED)


class Publication(models.Model):
    """Um conteudo recebido do PubliBot: artigo ou resposta a pergunta.

    O site so LE esta tabela. Quem grava e a rota /publish/ (e /publications/
    <id>/ na atualizacao), com o HTML ja sanitizado.

    O indice UNICO em `idempotency_key` impede publicacao duplicada: no
    timeout classico (o site grava, a resposta se perde, o PubliBot repete),
    a segunda chegada devolve a primeira. A restricao fica no BANCO porque
    duas requisicoes simultaneas passariam por qualquer checagem em Python.
    """

    class Kind(models.TextChoices):
        ARTICLE = "article", "Artigo"
        QA = "qa", "Resposta"

    class Status(models.TextChoices):
        PUBLISHED = "published", "Publicado"
        DRAFT = "draft", "Rascunho"
        SCHEDULED = "scheduled", "Agendado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.UUIDField(unique=True)

    kind = models.CharField(max_length=10, choices=Kind.choices)
    title = models.CharField(max_length=300, blank=True)
    slug = models.SlugField(max_length=300, blank=True, db_index=True)
    html_content = models.TextField()
    excerpt = models.TextField(blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    focus_keyword = models.CharField(max_length=120, blank=True)
    language = models.CharField(max_length=10, default="pt-br")

    author_name = models.CharField(max_length=150, blank=True)
    author_credentials = models.CharField(max_length=200, blank=True)
    # Identidade estavel do autor no PubliBot: liga a publicacao a foto
    # recebida depois (AuthorPhoto), mesmo que o nome mude.
    author_reference = models.UUIDField(null=True, blank=True, db_index=True)
    reviewed_by = models.CharField(max_length=150, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    content_disclosure = models.TextField(blank=True)

    canonical_source = models.URLField(max_length=500, blank=True)
    # A capa chega por URL (no PubliBot) e e baixada para o site: o contrato
    # pede servir do proprio dominio, sem hotlink. Use `capa_url` no template.
    cover_image_url = models.URLField(max_length=500, blank=True)
    cover_image_alt = models.CharField(max_length=300, blank=True)
    cover_image_sha256 = models.CharField(max_length=64, blank=True)
    cover_image = models.ImageField(upload_to="publibot/capas/", blank=True)

    # Perguntas frequentes, separadas do corpo: [{"question", "answer_html"}],
    # ja sanitizadas. Onde e como mostrar e decisao do template.
    faq = models.JSONField(default=list, blank=True)

    # Onde vai o bloco da chamada para a oferta: "none", "end" ou "inline".
    # O template usa as tags {% corpo_com_chamada %} e {% chamada_no_fim %}.
    call_to_action = models.CharField(max_length=8, default="end")

    # "Leia tambem": [{"remote_id", "title", "url"}], ja conferidos.
    related_articles = models.JSONField(default=list, blank=True)

    # Resposta a pergunta: o id da VisitorQuestion respondida.
    question_id = models.CharField(max_length=120, blank=True, db_index=True)

    post_status = models.CharField(max_length=20, default=Status.PUBLISHED)
    publish_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    # Atualizacoes: quantas vezes o conteudo foi substituido, quando, e a
    # chave da ultima (reenviar a mesma chave nao aplica de novo).
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(null=True, blank=True)
    last_update_key = models.UUIDField(null=True, blank=True)

    objects = PublicationQuerySet.as_manager()

    class Meta:
        verbose_name = "publicacao do PubliBot"
        verbose_name_plural = "publicacoes do PubliBot"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title or f"{self.kind} {self.pk}"

    # -- para o template -------------------------------------------------------

    def get_absolute_url(self) -> str:
        from publibot_core.conf import valor

        if self.kind == self.Kind.QA:
            modelo = valor("PUBLIBOT_QA_PATH")
        else:
            modelo = valor("PUBLIBOT_ARTICLE_PATH")
        return modelo.format(slug=self.slug or self.pk, id=self.pk, question_id=self.question_id)

    @property
    def url(self) -> str:
        """O endereco completo, que volta ao PubliBot."""
        from publibot_core.conf import valor

        return valor("PUBLIBOT_PUBLIC_URL").rstrip("/") + self.get_absolute_url()

    @property
    def capa_url(self) -> str:
        """A capa servida pelo site; enquanto nao baixou, a URL de origem."""
        if self.cover_image:
            return self.cover_image.url
        return self.cover_image_url

    @property
    def data_de_atualizacao(self):
        """A ultima atualizacao do conteudo (para dateModified e o sitemap)."""
        return self.updated_at or self.data_de_publicacao

    @property
    def data_de_publicacao(self):
        """Quando o conteudo foi (ou sera) ao ar: a data para mostrar e ordenar."""
        return self.published_at or self.publish_at or self.created_at

    @property
    def chamada_no_fim(self) -> bool:
        return self.call_to_action in {"end", "inline"}

    def html_com_chamada(self, bloco: str) -> str:
        """O corpo, com o bloco do site no lugar da marca (so no modo inline)."""
        from publibot_core.sanitize import ELEMENTO_DA_CHAMADA

        if self.call_to_action != "inline":
            return self.html_content.replace(ELEMENTO_DA_CHAMADA, "")
        return self.html_content.replace(ELEMENTO_DA_CHAMADA, bloco, 1)

    @property
    def foto_do_autor(self):
        """A AuthorPhoto do autor, ou None."""
        if self.author_reference is None:
            return None
        return AuthorPhoto.objects.filter(author_reference=self.author_reference).first()


class VisitorQuestion(models.Model):
    """Pergunta deixada por um visitante. O SITE grava (o formulario e dele).

    O PubliBot busca as pendentes, confirma o recebimento (acknowledged_at) e,
    depois da revisao humana, publica a resposta como Publication kind="qa" —
    o que preenche `answered_at`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField(max_length=500)
    author_name = models.CharField(max_length=150, blank=True)
    # Sem consentimento registrado, o nome nao vai para o PubliBot.
    consent_at = models.DateTimeField(null=True, blank=True)

    submitted_at = models.DateTimeField(default=timezone.now)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "pergunta de visitante"
        verbose_name_plural = "perguntas de visitantes"
        ordering = ["submitted_at"]
        indexes = [models.Index(fields=["acknowledged_at", "answered_at"])]

    def __str__(self) -> str:
        return self.question_text[:60]

    @property
    def resposta(self):
        """A Publication que responde esta pergunta, se ja publicada."""
        return Publication.objects.respostas_visiveis().filter(question_id=str(self.pk)).first()


class AuthorPhoto(models.Model):
    """Foto de perfil de um autor, recebida pela rota /author-photos/.

    Pela `author_reference` (estavel), e nao pelo nome: renomear um autor nao
    cria outra foto. O sha256 evita receber o mesmo arquivo de novo.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author_reference = models.UUIDField(unique=True)
    sha256 = models.CharField(max_length=64)
    image = models.ImageField(upload_to="publibot/autores/")
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "foto de autor"
        verbose_name_plural = "fotos de autor"
        ordering = ["-received_at"]

    def __str__(self) -> str:
        return str(self.author_reference)
