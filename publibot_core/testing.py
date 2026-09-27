"""Para testar o site: assinar uma requisicao como o PubliBot assina.

from publibot_core.testing import cabecalhos_assinados
corpo = json.dumps(dados).encode()
client.post("/api/v1/publish/", corpo, content_type="application/json",
            **cabecalhos_assinados(corpo, idempotency_key=str(uuid.uuid4())))
"""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid

from publibot_core import conf


def cabecalhos_assinados(corpo: bytes = b"", *, idempotency_key: str = "", **extra) -> dict:
    """Os cabecalhos do contrato, no formato do test client do Django."""
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex
    digest = hashlib.sha256(corpo or b"").hexdigest()
    base = f"{timestamp}.{nonce}.{digest}"
    segredo = conf.valor("PUBLIBOT_SIGNING_SECRET").encode()
    cabecalhos = {
        "HTTP_X_API_KEY": conf.valor("PUBLIBOT_API_KEY"),
        "HTTP_X_TIMESTAMP": timestamp,
        "HTTP_X_NONCE": nonce,
        "HTTP_X_SIGNATURE": "v1=" + hmac.new(segredo, base.encode(), hashlib.sha256).hexdigest(),
    }
    if idempotency_key:
        cabecalhos["HTTP_IDEMPOTENCY_KEY"] = idempotency_key
    cabecalhos.update(extra)
    return cabecalhos
