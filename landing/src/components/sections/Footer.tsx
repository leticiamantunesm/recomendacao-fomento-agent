const columns = [
  {
    title: "Produto",
    links: [
      { href: "#produto", label: "Visão geral" },
      { href: "#como-funciona", label: "Como funciona" },
      { href: "#demonstracao", label: "Demonstração" },
      { href: "/docs", label: "Documentação" },
    ],
  },
  {
    title: "Institucional",
    links: [
      { href: "#publico", label: "Público-alvo" },
      { href: "#seguranca", label: "Segurança e LGPD" },
      { href: "/login.html", label: "Acessar painel" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "#seguranca", label: "Política de Privacidade" },
      { href: "#seguranca", label: "LGPD" },
      { href: "mailto:contato@sads.local", label: "Contato" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="bg-navy-950 text-white">
      <div className="section-shell grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <div className="flex items-center gap-3">
            <img src="/sads-logo.png" alt="" className="h-11 w-auto" width={88} height={88} />
            <span className="font-display text-sm font-bold tracking-[0.18em]">SADS</span>
          </div>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-white/65">
            Sistema de Apoio à Decisão para Fomento à Inovação — análise de projetos e recomendação
            explicável de programas.
          </p>
        </div>
        {columns.map((col) => (
          <div key={col.title}>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-cyan-soft">
              {col.title}
            </p>
            <ul className="mt-4 space-y-2">
              {col.links.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-white/70 transition-colors hover:text-white"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-white/10">
        <div className="section-shell flex flex-col gap-2 py-5 text-xs text-white/45 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} SADS. Uso acadêmico / protótipo TCC.</p>
          <p>Scores são heurísticos e não substituem leitura integral do edital.</p>
        </div>
      </div>
    </footer>
  );
}
