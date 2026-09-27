"""As tabelas que o site usa: Publication, VisitorQuestion e AuthorPhoto.

As outras (leitura por dia, conversoes, nonces) sao da propria biblioteca e
ficam em `_internos`, fora deste modulo de proposito: o site nao le nem grava
nelas. Ver docs/PARA_IA.md.
"""

from publibot_core.models import _internos  # noqa: F401  (registra as tabelas internas)
from publibot_core.models.publicos import AuthorPhoto, Publication, VisitorQuestion

__all__ = ["AuthorPhoto", "Publication", "VisitorQuestion"]
