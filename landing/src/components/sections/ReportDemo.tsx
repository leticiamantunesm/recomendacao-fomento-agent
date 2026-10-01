import { Section } from "@/components/ui/Section";
import { ReportMockup } from "@/components/sections/ReportMockup";

export function ReportDemo() {
  return (
    <Section
      id="demonstracao"
      tone="muted"
      eyebrow="Demonstração"
      title="Veja o valor do relatório antes de criar conta"
      lead="Exemplo ilustrativo do que a equipe recebe após o upload: ranking, score, lacunas e encaminhamentos."
    >
      <div className="grid items-start gap-8 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="space-y-5">
          <div className="surface-card p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
              Projeto enviado
            </p>
            <p className="mt-2 font-display text-lg font-bold text-navy-900">
              Desenvolvimento de sensores IoT para agricultura de precisão
            </p>
            <p className="mt-2 text-sm text-ink-soft">PDF · 18 páginas · TRL 4–5 · Empresa EPP</p>
          </div>
          <div className="rounded-2xl border border-dashed border-paper-line bg-white p-5">
            <p className="text-sm leading-relaxed text-ink-soft">
              A análise cruza o texto do projeto com o corpus indexado (FINEP e demais fontes
              configuradas), avalia elegibilidade e devolve um dossiê navegável — útil para
              priorizar onde vale a pena escrever a proposta completa.
            </p>
            <ol className="mt-4 space-y-2 text-sm text-navy-900">
              <li>1. Ranking ordenado por aderência</li>
              <li>2. Explicação do score por critério</li>
              <li>3. Lacunas e plano de ação</li>
            </ol>
          </div>
        </div>
        <ReportMockup large />
      </div>
    </Section>
  );
}
