"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";

const links = [
  { href: "#produto", label: "Produto" },
  { href: "#como-funciona", label: "Como funciona" },
  { href: "#recursos", label: "Recursos" },
  { href: "#publico", label: "Público-alvo" },
  { href: "#demonstracao", label: "Demonstração" },
];

export function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-paper-line/80 bg-white/90 backdrop-blur-md">
      <div className="section-shell flex h-16 items-center justify-between gap-4">
        <a href="/" className="flex items-center gap-3" aria-label="SADS — página inicial">
          <img
            src="/sads-logo.png"
            alt=""
            className="h-10 w-auto"
            width={80}
            height={80}
          />
          <span className="hidden font-display text-sm font-bold tracking-[0.18em] text-navy-900 sm:inline">
            SADS
          </span>
        </a>

        <nav className="hidden items-center gap-6 lg:flex" aria-label="Principal">
          {links.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sm font-medium text-ink-soft transition-colors hover:text-navy-900"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2 sm:flex">
          <Button href="/login.html" variant="ghost" size="md">
            Login
          </Button>
          <Button href="/register.html" variant="primary" size="md">
            Analisar Projeto
          </Button>
        </div>

        <button
          type="button"
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-paper-line lg:hidden"
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((v) => !v)}
        >
          <span className="sr-only">Abrir menu</span>
          <span aria-hidden className="text-lg leading-none">
            {open ? "×" : "☰"}
          </span>
        </button>
      </div>

      {open ? (
        <div id="mobile-nav" className="border-t border-paper-line bg-white lg:hidden">
          <nav className="section-shell flex flex-col gap-1 py-3" aria-label="Mobile">
            {links.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-ink-soft hover:bg-paper"
                onClick={() => setOpen(false)}
              >
                {item.label}
              </a>
            ))}
            <div className="mt-2 flex flex-col gap-2 border-t border-paper-line pt-3">
              <Button href="/login.html" variant="secondary">
                Login
              </Button>
              <Button href="/register.html" variant="primary">
                Analisar Projeto
              </Button>
            </div>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
