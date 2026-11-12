# SADS — Segurança e privacidade · Roteiro para Canva

Uso: copiar bloco a bloco no Canva (Magic Design / texto → slide).  
1 mensagem por bloco · pouco texto · pronto para banca.

---

## SLIDE — Título

**Título:** Segurança e privacidade no SADS  
**Subtítulo:** Como o PoC trata dados de projetos e o que ainda evolui no TCC

**Mensagem:**  
Uma recomendação útil precisa ser **confiável** — técnica e eticamente.

---

## SLIDE — Princípio

**Título:** O que protegemos

**Três pontos (máx.):**
1. **Projetos da organização** — PDFs e formulários são dados sensíveis de negócio  
2. **Identidade dos usuários** — login, senha e sessão por organização  
3. **Separação de propósitos** — corpus de editais ≠ documentos privados

**Mensagem:**  
Finalidade clara: apoiar a decisão de fomento — não treinar modelo com o projeto do cliente.

---

## SLIDE — Multi-tenant

**Título:** Isolamento lógico por organização

**Diagrama:**
```text
Empresa A (company_id)
  → funcionários, projetos, documentos, aplicações

Empresa B (company_id)
  → outro espaço lógico — dados não se misturam
```

**O que já existe:**
- Tabelas com `company_id`
- Sessão autentica empresa + usuário
- Dashboard e fluxo amarrados à organização logada

**Mensagem:**  
Multi-tenant = cada organização vê **o seu** espaço.

---

## SLIDE — Autenticação (PoC)

**Título:** Quem acessa o painel

**Implementado:**
- Cadastro da organização + admin
- Login com empresa + e-mail + senha
- Senha armazenada com **hash (PBKDF2)** — não em texto puro
- Token de sessão assinado (HMAC)
- Fluxo de “esqueci a senha” (SMTP opcional / link em desenvolvimento)

**Planejado (TCC):**
- SSO / OAuth corporativo
- Permissões por perfil (RBAC): admin, analista, leitura

**Mensagem:**  
Hoje: autenticação por senha. Amanhã: identidade institucional + papéis.

---

## SLIDE — Dados do projeto (PoC)

**Título:** O que acontece com o PDF do projeto

**Faça / Não faça (dois lados):**

| No PoC | Não ocorre |
|--------|------------|
| Extração local de texto | Treino / fine-tuning com o projeto |
| Similaridade + scoring no servidor | Projeto no corpus público de editais |
| Ranking e relatório para a empresa | Envio a API de LLM generativo |

**Frase-chave:**  
`LLM_PROVIDER=none` → geração por **template local**, sem ChatGPT/API paga no fluxo atual.

**Mensagem:**  
O projeto entra na **análise em tempo de uso** — não vira dado de treino nem corpus compartilhado.

---

## SLIDE — Corpus vs projeto

**Título:** Duas bases, dois propósitos

**Diagrama:**
```text
Corpus FINEP (público / editais)
        ↕ similaridade + regras
Projeto da empresa (privado / company_id)
```

**Pontos:**
- Editais: coletados e indexados para matching  
- Projetos: ficam no tenant da organização  
- Relatório pode **linkar** o edital oficial — sem expor o PDF a terceiros

**Mensagem:**  
Recomendação cruzando **público** com **privado**, sem misturar os acervos.

---

## SLIDE — LGPD (honestidade)

**Título:** LGPD — alinhamento e maturidade

**Já refletido no desenho:**
- Finalidade definida (recomendação de fomento)
- Minimização (só o necessário para analisar)
- Isolamento por organização

**Ainda em evolução:**
- Política formal publicada e direitos do titular (acesso, exclusão) de ponta a ponta
- Hardening: autorização server-side em **todas** as rotas de projeto
- Testes de segurança cross-tenant

**Não dizer na banca:**
- “LGPD 100%”
- “Dados nunca vazam”
- “Já estamos em produção hardened”

**Mensagem:**  
Arquitetura **pensada** em privacidade; conformidade documental e hardening = roadmap do TCC.

---

## SLIDE — Riscos e limites

**Título:** Limitações que assumimos

**Chips (máx. 5):**
- Authz ainda **parcial** em algumas rotas da API (prioridade de hardening)
- Qualidade depende do catálogo FINEP atualizado
- PDF escaneado / texto fraco → formulário manual
- Score **não garante** aprovação no edital
- Texto do upload pode influenciar retrieval (confiança no usuário autenticado)

**Mensagem:**  
Transparência de limite = credibilidade acadêmica.

---

## SLIDE — Próximos controles

**Título:** Como vamos reforçar a segurança

| Controle | Benefício |
|----------|-----------|
| SSO / OAuth | Menos senha local; identidade da instituição |
| RBAC por perfil | Minimização: cada um vê só o necessário |
| Auth obrigatória nas rotas de projeto | Impede acesso cruzado entre tenants |
| Chat LLM (se vier) | Ollama local **ou** API com retenção zero / DPA; só trechos; opt-in; **sem treino** com projeto |
| Testes de segurança | Validar isolamento e regressões |

**Mensagem:**  
Chat com LLM, se entrar, será com **controle explícito de dados** — não “ligar GPT e mandar o PDF inteiro”.

---

## SLIDE — Frase de fechamento

**Título:** Em uma frase

**Texto central:**  
No PoC do SADS: análise no nosso fluxo + corpus de editais; **sem envio a APIs de LLM**; projeto **não treina** modelo e **não entra** no corpus público.

**Complemento (1 linha):**  
O SADS apoia a decisão — não substitui especialista nem a leitura oficial do edital.

---

## Notas para a fala (~45–60 s)

1. Abrir com o princípio: projeto confidencial ≠ corpus de editais.  
2. Mostrar multi-tenant + senha/hash/token.  
3. Enfatizar `LLM none` e “não treina”.  
4. Ser honesto: LGPD e authz ainda evoluem.  
5. Fechar com roadmap (SSO, RBAC, hardening, chat seguro).

---

## Checklist anti-erro (banca)

- [ ] Não prometer “zero risco”  
- [ ] Não dizer que usamos GPT no PoC  
- [ ] Não dizer que AHP/TOPSIS já estão no scoring  
- [ ] Separar: **implementado** × **planejado**  
- [ ] Se perguntarem authz: admitir parcial + citar hardening como próximo passo
