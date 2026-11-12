"""Smoke-test da integração BNDES (server-side).

Uso:
  python -m scripts.probe_bndes_api
  python -m scripts.probe_bndes_api --public-only
  python -m scripts.probe_bndes_api --portfolio

Não imprime tokens nem secrets.
"""

from __future__ import annotations

import argparse
import logging
import sys

from app.config import get_settings
from app.integrations.bndes import (
    BndesClient,
    BndesContractNotConfiguredError,
)
from app.integrations.bndes.errors import BndesApiError

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("probe_bndes_api")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe BNDES API integration")
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Só testa o catálogo público do Navegador (sem OAuth).",
    )
    parser.add_argument(
        "--portfolio",
        action="store_true",
        help="Testa POST Portfólio /obterconfiguracaooperacional (requer OAuth).",
    )
    parser.add_argument(
        "--payload",
        default=None,
        help="String opcional do campo body.payload (Swagger Portfólio).",
    )
    args = parser.parse_args(argv)
    settings = get_settings()
    exit_code = 0

    with BndesClient(settings) as client:
        try:
            public = client.list_public_linhas_programas()
            logger.info(
                "public_linhas ok status=%s items=%s",
                public.status_code,
                len(public.items),
            )
        except BndesApiError as exc:
            logger.error("public_linhas falhou: %s", exc)
            if args.public_only:
                return 1
            exit_code = max(exit_code, 1)

        if args.public_only:
            return exit_code

        if args.portfolio or not args.public_only:
            try:
                result = client.obter_configuracao_operacional(payload=args.payload)
                logger.info(
                    "portfolio_obter_config ok status=%s type=%s",
                    result.status_code,
                    type(result.data).__name__,
                )
            except BndesContractNotConfiguredError as exc:
                logger.warning(
                    "Portfolio OAuth incompleto (defina BNDES_CLIENT_ID/SECRET/TOKEN_URL): %s",
                    exc,
                )
                exit_code = max(exit_code, 2)
            except BndesApiError as exc:
                logger.error("portfolio_obter_config falhou: %s", exc)
                exit_code = max(exit_code, 1)

            if args.portfolio:
                return exit_code

        try:
            result = client.get_financing_options()
            logger.info(
                "opcoes_financiamento ok status=%s type=%s",
                result.status_code,
                type(result.data).__name__,
            )
        except BndesContractNotConfiguredError as exc:
            logger.warning(
                "Contrato Opções de financiamento incompleto (opcional): %s",
                exc,
            )
            # Portfolio é o contrato principal agora; opções fica warning sem falhar hard
            # se portfolio já rodou. Mantém 2 só se portfolio também falhou por contrato.
            if exit_code == 0:
                exit_code = 2
        except BndesApiError as exc:
            logger.error("opcoes_financiamento falhou: %s", exc)
            exit_code = max(exit_code, 1)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
