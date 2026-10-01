import { Button } from "@/components/ui/Button";
import { ReportMockup } from "@/components/sections/ReportMockup";

export function Hero() {
  return (
    <section id="produto" className="relative overflow-hidden border-b border-paper-line bg-white">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(46,199,255,0.08),transparent_45%)]" />
      <div className="section-shell relative grid items-center gap-12 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
        <div>
          <p className="eyebrow">Sistema de Apoio à Decisão</p>
          <h1 className="mt-4 font-display text-4xl font-bold leading-[1.08] tracking-tight text-navy-900 sm:text-5xl lg:text-[3.25rem]">
            Descubra os melhores programas de fomento para o seu projeto — com clareza sobre o porquê.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-relaxed text-ink-soft sm:text-lg">
            O SADS analisa o PDF do projeto e o perfil da organização, cruza critérios de
            elegibilidade e entrega um ranking explicável de programas — com lacunas e plano de ação
            para submissão.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button href="/register.html" size="lg">
              Analisar meu projeto
            </Button>
            <Button href="#demonstracao" variant="secondary" size="lg">
              Ver demonstração
            </Button>
          </div>
          <dl className="mt-10 grid max-w-lg grid-cols-3 gap-4 border-t border-paper-line pt-8">
            {[
              ["Minutos", "em vez de semanas"],
              ["Explicável", "score por critério"],
              ["Multi-fonte", "FINEP e mais"],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="font-display text-sm font-bold text-navy-900">{k}</dt>
                <dd className="mt-1 text-xs text-ink-faint">{v}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="lg:pl-4">
          <ReportMockup compact />
        </div>
      </div>
    </section>
  );
}
