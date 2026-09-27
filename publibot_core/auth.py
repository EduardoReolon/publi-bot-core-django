"""Verificacao da assinatura das requisicoes recebidas.

Cada decisao aqui corresponde a uma regra normativa do contrato. Os comentarios
explicam o porque, porque quem copiar este arquivo precisa entender o que nao
pode simplificar.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone

from publibot_core import conf

JANELA_DE_TEMPO_SEGUNDOS = 300
RETENCAO_DE_NONCE_SEGUNDOS = 600

# Resposta unica para chave ausente, malformada ou incorreta. Mensagens
# diferentes vazariam a mesma informacao por outro canal — quem tenta descobre
# se a chave existe pelo texto do erro.
RESPOSTA_DE_NEGACAO = {
    "error": {
        "code": "invalid_api_key",
        "message": "Credencial invalida.",
        "details": {},
    }
}


def negar() -> JsonResponse:
    return JsonResponse(RESPOSTA_DE_NEGACAO, status=401)


def _chaves_aceitas() -> list[str]:
    """A chave atual e, durante uma rotacao, a anterior.

    Sem a janela dupla, rotacionar exigiria trocar os dois lados no mesmo
    instante — o que na pratica significa uma janela de indisponibilidade.
    """
    chaves = [conf.valor("PUBLIBOT_API_KEY")]
    anterior = conf.valor("PUBLIBOT_API_KEY_PREVIOUS")
    if anterior:
        chaves.append(anterior)
    return [c for c in chaves if c]


def conferir_assinatura(request) -> JsonResponse | None:
    """Devolve None quando a requisicao e valida, ou a resposta de negacao."""
    recebida = request.headers.get("X-API-KEY", "")
    timestamp = request.headers.get("X-Timestamp", "")
    nonce = request.headers.get("X-Nonce", "")
    assinatura = request.headers.get("X-Signature", "")

    # `compare_digest` sobre cada candidata. A escrita natural
    # (`if recebida not in chaves`) e curto-circuitada byte a byte: o tempo de
    # resposta revela quantos bytes iniciais estao corretos.
    if not any(hmac.compare_digest(recebida, valida) for valida in _chaves_aceitas()):
        return negar()

    if not _no_prazo(timestamp) or not nonce or len(nonce) > 128:
        return negar()

    segredo = conf.valor("PUBLIBOT_SIGNING_SECRET")
    if not segredo:
        return negar()

    # `request.body` e o corpo BRUTO, antes de qualquer interpretacao.
    # Reserializar o JSON antes de conferir produziria digests diferentes para
    # o mesmo conteudo, e a assinatura falharia de forma aparentemente
    # aleatoria.
    digest_do_corpo = hashlib.sha256(request.body or b"").hexdigest()
    base = f"{timestamp}.{nonce}.{digest_do_corpo}"
    esperada = "v1=" + hmac.new(segredo.encode(), base.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(esperada, assinatura):
        return negar()

    # O nonce so e gravado depois da assinatura conferida: quem nao tem o
    # segredo nao consegue encher a tabela.
    if not _nonce_novo(nonce):
        return negar()

    return None


def _no_prazo(timestamp: str) -> bool:
    try:
        return abs(time.time() - float(timestamp)) <= JANELA_DE_TEMPO_SEGUNDOS
    except (TypeError, ValueError):
        return False


def _nonce_novo(nonce: str) -> bool:
    """Grava o nonce; False se ele ja foi usado.

    O INSERT com indice unico decide, inclusive entre duas requisicoes
    simultaneas — ler antes e gravar depois deixaria as duas passarem. Os
    antigos (fora da janela, que ja recusa pelo relogio) sao apagados aqui.
    """
    from publibot_core.models._internos import UsedNonce

    agora = timezone.now()
    UsedNonce.objects.filter(
        created_at__lt=agora - timedelta(seconds=RETENCAO_DE_NONCE_SEGUNDOS)
    ).delete()
    try:
        with transaction.atomic():
            UsedNonce.objects.create(nonce=nonce, created_at=agora)
    except IntegrityError:
        return False
    return True
