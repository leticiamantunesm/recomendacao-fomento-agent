import { Section } from "@/components/ui/Section";

const items = [
  {
    title: "Multi-tenant",
    text: "Isolamento lógico por organização. Dados de uma empresa não se misturam com os de outra.",
  },
  {
    title: "Controle de acesso (RBAC)",
    text: "Perfis e permissões para separar quem cadastra, quem analisa e quem apenas consulta.",
  },
  {
    title: "Autenticação corporativa",
    text: "Roadmap com OAuth/SSO para integrar identidade institucional na Fase B.",
  },
  {
    title: "LGPD",
    text: "Tratamento alinhado a finalidade, minimização e direitos do titular — com política publicada.",
  },
];

export function Security() {
  return (
    <Section
      id="seguranca"
      tone="dark"
      eyebrow="Segurança e conformidade"
      title="Construído para ambientes em que confiança é requisito"
      lead="Empresas, ICTs e universidades precisam de trilha clara sobre quem acessa o quê — e por quê."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((item) => (
          <article
            key={item.title}
            className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm"
          >
            <h3 className="font-display text-base font-bold text-white">{item.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-white/70">{item.text}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
