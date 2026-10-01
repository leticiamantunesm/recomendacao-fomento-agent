import { Section } from "@/components/ui/Section";

const items = [
  {
    title: "Ranking de programas",
    text: "Ordem objetiva de aderência entre o projeto e chamadas disponíveis.",
  },
  {
    title: "Score explicável",
    text: "Pontuação decomponível por critério — não uma caixa-preta.",
  },
  {
    title: "Critérios atendidos",
    text: "Visão clara do que já está alinhado à elegibilidade e ao escopo.",
  },
  {
    title: "Critérios faltantes",
    text: "Identificação do que ainda bloqueia ou enfraquece a candidatura.",
  },
  {
    title: "Lacunas do projeto",
    text: "Gaps documentais e de conteúdo priorizados por impacto.",
  },
  {
    title: "Plano de ação",
    text: "Sequência sugerida para reforçar a proposta antes da submissão.",
  },
  {
    title: "Histórico de análises",
    text: "Reavaliações e comparações ao longo do ciclo do projeto.",
  },
  {
    title: "Recomendação com IA",
    text: "Cruzamento semântico do texto do projeto com o corpus de editais.",
  },
];

export function WhatYouGet() {
  return (
    <Section
      id="recursos"
      tone="muted"
      eyebrow="O que você recebe"
      title="Um dossiê de decisão — não apenas uma lista de editais"
      lead="Cada análise entrega artefatos que a equipe pode usar em comitês internos, com rastreabilidade do raciocínio."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((item) => (
          <article key={item.title} className="surface-card p-5">
            <div className="mb-4 h-1 w-8 rounded-full bg-cyan" aria-hidden />
            <h3 className="font-display text-base font-bold text-navy-900">{item.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">{item.text}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
