import { Section } from "@/components/ui/Section";

const audiences = [
  {
    title: "Startups",
    text: "Identifique chamadas compatíveis com estágio, porte e tema — sem dispersar o time em triagem interminável.",
  },
  {
    title: "Empresas e P&D",
    text: "Padronize a avaliação de pipeline de inovação e compartilhe evidências com liderança e compliance.",
  },
  {
    title: "ICTs e centros de pesquisa",
    text: "Acelere o matching entre projetos de P&D e instrumentos de fomento públicos e parcerias.",
  },
  {
    title: "Consultorias",
    text: "Escale a pré-análise de clientes com ranking explicável e histórico por organização.",
  },
  {
    title: "Universidades",
    text: "Apoie NITs e escritórios de projetos na priorização de submissões e na preparação documental.",
  },
];

export function Audience() {
  return (
    <Section
      id="publico"
      eyebrow="Público-alvo"
      title="Feito para quem decide onde investir esforço de captação"
      lead="Do empreendedor à diretoria de inovação: o SADS fala a linguagem de elegibilidade, prazo e competitividade."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {audiences.map((item) => (
          <article key={item.title} className="surface-card p-6">
            <h3 className="font-display text-lg font-bold text-navy-900">{item.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">{item.text}</p>
          </article>
        ))}
      </div>
      <p className="mt-8 text-sm text-ink-faint">
        Fontes suportadas na plataforma incluem FINEP, EMBRAPII, FAPESP, BNDES, incentivos fiscais e
        outros programas de inovação — conforme corpus indexado.
      </p>
    </Section>
  );
}
