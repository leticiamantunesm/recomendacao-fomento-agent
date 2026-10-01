import type { ReactNode } from "react";

type Props = {
  id?: string;
  eyebrow?: string;
  title: string;
  lead?: string;
  children: ReactNode;
  className?: string;
  tone?: "default" | "muted" | "dark";
};

const tones = {
  default: "bg-white",
  muted: "bg-paper",
  dark: "bg-navy-900 text-white",
};

export function Section({
  id,
  eyebrow,
  title,
  lead,
  children,
  className = "",
  tone = "default",
}: Props) {
  const dark = tone === "dark";
  return (
    <section id={id} className={`py-20 sm:py-24 ${tones[tone]} ${className}`}>
      <div className="section-shell">
        <div className="max-w-3xl">
          {eyebrow ? (
            <p className={`eyebrow ${dark ? "text-cyan-soft" : ""}`}>{eyebrow}</p>
          ) : null}
          <h2 className={`section-title mt-3 ${dark ? "text-white" : ""}`}>{title}</h2>
          {lead ? (
            <p className={`section-lead ${dark ? "text-white/70" : ""}`}>{lead}</p>
          ) : null}
        </div>
        <div className="mt-12">{children}</div>
      </div>
    </section>
  );
}
