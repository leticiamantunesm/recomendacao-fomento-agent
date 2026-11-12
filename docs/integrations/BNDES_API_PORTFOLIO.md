# Integração BNDES — API Portfólio (tentativa TCC)

**Status: tentativa documentada — autorização na Loja de APIs não obtida.**

Ver **ADR-009** em `docs/DECISOES_ARQUITETURAIS.md`.

## O que foi feito

1. Análise do Swagger 2.0 fornecido (homolog):
   - Host: `gateway-h.apis.bndes.gov.br`
   - `POST /produtos/v1/obterconfiguracaooperacional`
   - Body opcional `{ "payload": "<string>" }`
2. Client server-side em `app/integrations/bndes/` (OAuth configurável + método tipado).
3. Testes unitários com mock HTTP (`tests/test_bndes_client.py`).

## O que falhou

- Cadastro/assinatura na [Loja de APIs BNDES](https://apis.bndes.gov.br/store/) **não autorizada** no prazo.
- Guias no [Portal do Desenvolvedor](https://portal.apis.bndes.gov.br/) permanecem em **acesso restrito** sem autenticação aprovada.
- Sem `client_id` / `client_secret` / `token URL` oficiais válidos para o ambiente do TCC, a chamada real não foi concluída.

## Decisão de produto

O motor de recomendação **não** usa esta API. O BNDES aparece só como **opção ampla** de crédito (sem programas específicos). Código e este documento ficam como evidência de tentativa e limitação externa — útil para a discussão de resultados do TCC.
