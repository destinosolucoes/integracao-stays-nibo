"""
Camada de seguranca da integracao Stays -> Nibo.

Todas as protecoes sao ativadas por variavel de ambiente, para que o deploy
desta versao NAO quebre nenhum chamador existente:

- INTEGRATION_API_KEY
    Protege /api/create-reservation e /api/delete-reservation.
    * Nao definida  -> endpoints continuam abertos (comportamento antigo),
                       com aviso no log a cada chamada.
    * Definida      -> exige o cabecalho `x-api-key: <valor>`
                       (ou `Authorization: Bearer <valor>`); caso contrario 401.

- STAYS_WEBHOOK_SIGNATURE_MODE  (off | log | enforce; padrao: log)
    Validacao do cabecalho `x-stays-signature` do webhook.
    O formato exato da assinatura da Stays nao esta na documentacao publica,
    entao a verificacao testa HMAC-SHA256 do corpo bruto com
    STAYS_WEBHOOK_SECRET (ou, na falta dele, STAYS_CLIENT_SECRET), em hex e
    base64.
    * off     -> nao verifica (comportamento antigo).
    * log     -> verifica e apenas registra no log se conferiu. Nao bloqueia.
    * enforce -> rejeita com 403 quando a assinatura nao confere.
    So mude para `enforce` depois de confirmar no log que as chamadas
    legitimas da Stays aparecem como "signature_valid=True".

- CORS_ALLOWED_ORIGINS
    Lista separada por virgula. Padrao: "*" (comportamento antigo).
"""

import base64
import hashlib
import hmac
import logging
from os import getenv

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


def _env(name, default=None):
    value = getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


# ---------------------------------------------------------------------------
# Chave de API dos endpoints manuais
# ---------------------------------------------------------------------------

def require_api_key(request: Request):
    """Dependencia FastAPI para os endpoints manuais."""
    expected = _env("INTEGRATION_API_KEY")

    if expected is None:
        logger.warning(
            "INTEGRATION_API_KEY nao configurada: %s aceito sem autenticacao.",
            request.url.path,
        )
        return

    provided = request.headers.get("x-api-key")
    if provided is None:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            provided = auth[7:].strip()

    if not provided or not hmac.compare_digest(provided, expected):
        logger.warning("Chamada sem chave valida em %s", request.url.path)
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------------------
# Assinatura do webhook da Stays
# ---------------------------------------------------------------------------

def _signature_mode():
    mode = (_env("STAYS_WEBHOOK_SIGNATURE_MODE", "log") or "log").lower()
    return mode if mode in ("off", "log", "enforce") else "log"


def _signature_matches(raw_body: bytes, signature: str) -> bool:
    secret = _env("STAYS_WEBHOOK_SECRET") or _env("STAYS_CLIENT_SECRET")
    if not secret or not signature:
        return False

    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).digest()
    candidates = {digest.hex(), base64.b64encode(digest).decode()}

    sig = signature.strip()
    if "=" in sig and sig.split("=", 1)[0].lower() in ("sha256", "hmac-sha256"):
        sig = sig.split("=", 1)[1]

    return any(hmac.compare_digest(sig, c) for c in candidates)


def check_webhook_signature(headers, raw_body: bytes):
    """Retorna True se a requisicao pode seguir. Levanta 403 em modo enforce."""
    mode = _signature_mode()
    if mode == "off":
        return True

    valid = _signature_matches(raw_body, headers.get("x-stays-signature", ""))
    logger.info("stays-webhook signature_valid=%s mode=%s", valid, mode)

    if not valid and mode == "enforce":
        raise HTTPException(status_code=403)
    return True


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

def cors_origins():
    raw = _env("CORS_ALLOWED_ORIGINS", "*")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["*"]
