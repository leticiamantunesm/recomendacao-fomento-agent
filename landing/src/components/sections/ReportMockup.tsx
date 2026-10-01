type Props = { compact?: boolean; large?: boolean };

const ranking = [
  { rank: 1, name: "Subvenção Econômica — FINEP", score: 92, tone: "high" },
  { rank: 2, name: "EMBRAPII", score: 85, tone: "high" },
  { rank: 3, name: "PRONINC", score: 78, tone: "mid" },
];

export function ReportMockup({ compact = false, large = false }: Props) {
  return (
    <aside
      className={[
        "surface-card overflow-hidden",
        large ? "shadow-panel" : "",
      ].join(" ")}
      aria-label="Prévia do relatório SADS"
    >
      <div className="flex items-center justify-between border-b border-paper-line bg-navy-900 px-4 py-3 text-white sm:px-5">
        <div>
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-cyan-soft">
            Relatório de recomendação
          </p>
          <p className="mt-0.5 text-sm font-semibold">Projeto Semicondutores Avançados</p>
        </div>
        <div className="rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold text-cyan-soft">
          Análise concluída
        </div>
      </div>

      <div className={`grid gap-4 p-4 sm:p-5 ${large ? "lg:grid-cols-[1.2fr_0.8fr]" : ""}`}>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Melhor oportunidade
          </p>
          <h3 className="mt-1 font-display text-lg font-bold text-navy-900">
            Subvenção Econômica — FINEP
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-ink-soft">
            Alta aderência temática, porte elegível e TRL compatível com a chamada vigente.
          </p>
          {!compact ? (
            <ul className="mt-4 space-y-2 text-sm text-ink-soft">
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan" />
                Escopo alinhado a inovação tecnológica
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan" />
                Documentação mínima parcialmente atendida
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                Lacuna: detalhar contrapartida financeira
              </li>
            </ul>
          ) : null}
        </div>

        <div className="flex flex-col items-center justify-center rounded-xl border border-paper-line bg-paper px-4 py-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Compatibilidade
          </p>
          <p className="mt-2 font-display text-4xl font-bold text-navy-900">92%</p>
          <p className="mt-1 text-xs font-medium text-emerald-700">Alta chance relativa</p>
          <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-white">
            <div className="h-full w-[92%] rounded-full bg-navy-900" />
          </div>
        </div>
      </div>

      <div className="border-t border-paper-line px-4 py-4 sm:px-5">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-faint">
          Ranking de programas
        </p>
        <ol className="space-y-2">
          {ranking.map((item) => (
            <li
              key={item.rank}
              className="flex items-center justify-between gap-3 rounded-xl border border-paper-line bg-white px-3 py-2.5"
            >
              <div className="flex min-w-0 items-center gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-navy-900 text-xs font-bold text-white">
                  {item.rank}
                </span>
                <span className="truncate text-sm font-medium text-navy-900">{item.name}</span>
              </div>
              <span
                className={`shrink-0 text-sm font-bold ${
                  item.tone === "high" ? "text-emerald-700" : "text-amber-700"
                }`}
              >
                {item.score}%
              </span>
            </li>
          ))}
        </ol>
      </div>
    </aside>
  );
}
