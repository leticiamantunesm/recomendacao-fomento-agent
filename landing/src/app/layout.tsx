import type { Metadata } from "next";
import { Inter, Montserrat } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const montserrat = Montserrat({
  subsets: ["latin"],
  variable: "--font-montserrat",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SADS — Sistema de Apoio à Decisão para Fomento à Inovação",
  description:
    "Analise projetos com IA, receba ranking explicável de programas de fomento, lacunas e plano de ação. FINEP, EMBRAPII, FAPESP, BNDES e mais.",
  icons: { icon: "/sads-logo.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${montserrat.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
