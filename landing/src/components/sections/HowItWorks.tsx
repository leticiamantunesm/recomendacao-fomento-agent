import { Section } from "@/components/ui/Section";

const steps = [
  {
    n: "01",
    title: "Cadastre a organização",
    text: "Informe CNPJ, porte, área de atuação e dados institucionais. O perfil alimenta a elegibilidade.",
  },
  {
    n: "02",
    title: "Envie o PDF do projeto",
    text: "Faça upload da proposta. O SADS extrai escopo, maturidade tecnológica e sinais de alinhamento.",
  },
  {
    n: "03",
    title: "Receba a análise automática",
    text: "Ranking de programas, score por critério, lacunas e justificativas — em minutos, não em semanas.",
  },
  {
    n: "04",
    title: "Planeje a submissão",
    text: "Use o plano de ação para priorizar ajustes documentais e aumentar a competitividade da proposta.",
  },
];

export function HowItWorks() {
  return (
    <Section
      id="como-funciona"
      eyebrow="Como funciona"
      title="Do PDF ao ranking em quatro etapas"
      lead="Fluxo pensado para áreas de inovação: rápido de operar, auditável e pronto para discussão com diretoria ou banca interna."
    >
      <ol className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {steps.map((step) => (
          <li key={step.n} className="surface-card relative p-5">
            <span className="font-display text-sm font-bold tracking-[0.12em] text-cyan">
              {step.n}
            </span>
            <h3 className="mt-3 font-display text-lg font-bold text-navy-900">{step.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">{step.text}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}
