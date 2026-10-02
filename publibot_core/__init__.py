"""O lado do site no contrato PubliBot /api/v1, como app Django instalavel.

Leia docs/PARA_IA.md (o que o site usa) e docs/IMPLANTACAO.md (como instalar).
"""

__version__ = "1.1.1"

VERSOES_DO_CONTRATO = ["v1"]

RECURSOS = [
    "idempotency",
    "hmac_signature",
    "cursor_pagination",
    "image_by_url",
    "author_photo",
    "qa",
    "reconciliation",
    "faq",
    "update",
    "call_to_action",
    "insights",
    "related_articles",
]
