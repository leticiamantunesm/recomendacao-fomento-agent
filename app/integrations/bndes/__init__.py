"""Cliente BNDES (Developers@BNDES + catálogo público do Navegador)."""

from app.integrations.bndes.client import BndesClient, BndesService
from app.integrations.bndes.errors import (
    BndesApiError,
    BndesAuthError,
    BndesContractNotConfiguredError,
    BndesHttpError,
    BndesRateLimitError,
    BndesTimeoutError,
)

__all__ = [
    "BndesClient",
    "BndesService",
    "BndesApiError",
    "BndesAuthError",
    "BndesContractNotConfiguredError",
    "BndesHttpError",
    "BndesRateLimitError",
    "BndesTimeoutError",
]
