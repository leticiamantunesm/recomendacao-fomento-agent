import { Header } from "@/components/sections/Header";
import { Hero } from "@/components/sections/Hero";
import { Problem } from "@/components/sections/Problem";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { WhatYouGet } from "@/components/sections/WhatYouGet";
import { Comparison } from "@/components/sections/Comparison";
import { ReportDemo } from "@/components/sections/ReportDemo";
import { Audience } from "@/components/sections/Audience";
import { Security } from "@/components/sections/Security";
import { FinalCta } from "@/components/sections/FinalCta";
import { Footer } from "@/components/sections/Footer";
import { SessionRedirect } from "@/components/SessionRedirect";

export default function HomePage() {
  return (
    <>
      <SessionRedirect />
      <Header />
      <main>
        <Hero />
        <Problem />
        <HowItWorks />
        <WhatYouGet />
        <Comparison />
        <ReportDemo />
        <Audience />
        <Security />
        <FinalCta />
      </main>
      <Footer />
    </>
  );
}
