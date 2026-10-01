import { Button } from "@/components/ui/Button";

export function FinalCta() {
  return (
    <section className="border-y border-paper-line bg-paper py-20 sm:py-24">
      <div className="section-shell max-w-3xl text-center">
        <p className="eyebrow mx-auto">Comece agora</p>
        <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-navy-900 sm:text-4xl">
          Pronto para descobrir os melhores programas para o seu projeto?
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-ink-soft">
          Cadastre a organização, envie o PDF e receba um ranking explicável com lacunas e plano de
          ação.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Button href="/register.html" size="lg">
            Analisar Projeto
          </Button>
          <Button href="/register.html" variant="secondary" size="lg">
            Criar Conta
          </Button>
        </div>
      </div>
    </section>
  );
}
