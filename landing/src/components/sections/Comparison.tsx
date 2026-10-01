import { Section } from "@/components/ui/Section";

const rows = [
  ["Tempo para triagem", "Minutos", "Dias a semanas", "Dias, sob demanda"],
  ["Custo marginal por projeto", "Baixo e previsível", "Alto (horas internas)", "Alto (honorários)"],
  ["Escalabilidade", "Vários projetos em paralelo", "Limitada pela equipe", "Limitada por contrato"],
  ["Explicabilidade", "Score por critério + lacunas", "Depende do analista", "Depende do consultor"],
  ["LGPD e trilha", "Controles multi-tenant", "Variável", "Variável"],
  ["Centralização", "Histórico único na plataforma", "Planilhas e e-mails", "Relatórios pontuais"],
];

export function Comparison() {
  return (
    <Section
      id="diferenciais"
      eyebrow="Diferenciais"
      title="SADS frente à busca manual e às consultorias"
      lead="Não substitui julgamento humano nem banca oficial. Acelera a triagem, padroniza a evidência e reduz o custo de explorar opções."
    >
      <div className="overflow-x-auto rounded-2xl border border-paper-line bg-white shadow-soft">
        <table className="min-w-[720px] w-full border-collapse text-left text-sm">
          <caption className="sr-only">
            Comparativo entre SADS, busca manual e consultorias
          </caption>
          <thead>
            <tr className="border-b border-paper-line bg-paper">
              <th scope="col" className="px-4 py-3 font-semibold text-ink-faint">
                Critério
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-navy-900">
                SADS
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-ink-soft">
                Busca manual
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-ink-soft">
                Consultorias
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row[0]} className="border-b border-paper-line last:border-0">
                <th scope="row" className="px-4 py-3.5 font-medium text-navy-900">
                  {row[0]}
                </th>
                <td className="px-4 py-3.5 font-medium text-navy-900">{row[1]}</td>
                <td className="px-4 py-3.5 text-ink-soft">{row[2]}</td>
                <td className="px-4 py-3.5 text-ink-soft">{row[3]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}
