import { Section } from "@/components/ui/Section";

const pains = [
  {
    stat: "Dezenas",
    label: "de fontes dispersas",
    text: "Editais e programas espalhados entre FINEP, EMBRAPII, FAPs, BNDES e incentivos fiscais.",
  },
  {
    stat: "Semanas",
    label: "em triagem manual",
    text: "Equipes de P&D gastam tempo lendo chamadas sem saber se o projeto é elegível de fato.",
  },
  {
    stat: "Alto",
    label: "custo de consultoria",
    text: "Apoio especializado ajuda, mas não escala para múltiplos projetos e reavaliações.",
  },
  {
    stat: "Baixa",
    label: "explicabilidade",
    text: "Mesmo quando há uma indicação, falta clareza sobre critérios, gaps e próximo passo.",
  },
];

export function Problem() {
  return (
    <Section
      id="problema"
      tone="muted"
      eyebrow="O problema"
      title="Encontrar fomento certo ainda é lento, fragmentado e opaco"
      lead="Gestores de inovação enfrentam volume de editais, regras distintas de elegibilidade e pouca evidência para decidir onde investir esforço de submissão."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {pains.map((item) => (
          <article key={item.label} className="surface-card p-5">
            <p className="font-display text-3xl font-bold text-navy-900">{item.stat}</p>
            <p className="mt-1 text-sm font-semibold text-cyan">{item.label}</p>
            <p className="mt-3 text-sm leading-relaxed text-ink-soft">{item.text}</p>
          </article>
        ))}
      </div>
    </Section>
  );
}
