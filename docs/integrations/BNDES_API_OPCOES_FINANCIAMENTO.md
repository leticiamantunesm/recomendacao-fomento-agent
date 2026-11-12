# Integração BNDES — Opções de financiamento (tentativa TCC)

**Status: tentativa documentada — autorização na Loja de APIs não obtida.**

Ver **ADR-009** e `docs/integrations/BNDES_API_PORTFOLIO.md`.

## Resumo

A landing Developers@BNDES menciona a API “Opções de financiamento” (natureza, porte, prazo, valor) atrás de OAuth2 na Loja. Sem login/aprovação, o contrato OpenAPI (path, params, schema, token URL, scope) **não** ficou acessível publicamente.

O SADS:

- implementou um client genérico configurável por env (`app/integrations/bndes/`);
- **não** inventou endpoint;
- **não** ligou a API ao ranking/UI;
- após falha de autorização, passou a tratar BNDES apenas de forma **institucional ampla** no coletor e nos redirects de modernização.

## Lacunas que permaneceram

Token URL, scope, gateway de produção, path e schema da resposta — todos dependentes do Console pós-aprovação na Loja.
