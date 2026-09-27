"""Cursor de paginacao por (data, id), igual em qualquer banco.

A ordem e (data, id); o cursor diz "depois deste par". Filtrar so por id
(como se o UUID crescesse com o tempo) pularia ou repetiria linhas: UUID v4 e
aleatorio. O cursor e opaco para o PubliBot: ele so devolve o que recebeu.
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime

from django.db.models import Q


def cursor_de(objeto, campo_de_data: str) -> str:
    bruto = f"{getattr(objeto, campo_de_data).isoformat()}|{objeto.pk}"
    return base64.urlsafe_b64encode(bruto.encode()).decode()


def depois_do_cursor(consulta, cursor: str, campo_de_data: str):
    """A consulta a partir do cursor. Cursor invalido recomeca do inicio."""
    if not cursor:
        return consulta
    try:
        data, ident = base64.urlsafe_b64decode(cursor.encode()).decode().split("|", 1)
        data = datetime.fromisoformat(data)
        ident = uuid.UUID(ident)
    except (ValueError, UnicodeDecodeError):
        return consulta
    return consulta.filter(
        Q(**{f"{campo_de_data}__gt": data}) | Q(**{campo_de_data: data, "pk__gt": ident})
    )
