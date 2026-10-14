import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import {
  ArrowRight,
  Zap,
  Layers,
  Rocket,
  Globe,
  Shield,
  Cpu,
  Github,
  Twitter,
  ChevronRight,
  Star,
  Code2,
  Sparkles,
} from "lucide-react";
import SplineHero from "@/components/SplineHero";
import ScrollReveal from "@/components/ScrollReveal";

/* ── tiny sub-components ──────────────────────────────────────────── */

function NavBar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50">
      {/* subtle top glow line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />

      <div className="backdrop-blur-2xl bg-[#06060a]/60 border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:shadow-indigo-500/40 transition-all duration-300 group-hover:scale-105">
              <Zap className="w-4.5 h-4.5 text-white" />
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            <span className="text-lg font-bold tracking-tight text-white">
              Synth<span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">Team</span>
            </span>
          </Link>

          {/* center pill nav */}
          <div className="hidden md:flex items-center gap-1 bg-white/[0.04] border border-white/[0.06] rounded-full px-1.5 py-1">
            {[
              { label: "Features", href: "#features" },
              { label: "How it works", href: "#how" },
              { label: "Pricing", href: "#cta" },
            ].map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm text-white/50 hover:text-white hover:bg-white/[0.08] px-4 py-1.5 rounded-full transition-all duration-200"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* auth */}
          <div className="flex items-center gap-3">
            <SignedOut>
              <SignInButton>
                <button className="text-sm text-white/50 hover:text-white transition-colors px-3 py-1.5 cursor-pointer">
                  Sign In
                </button>
              </SignInButton>
              <Link
                href="/sign-up"
                className="group relative text-sm font-medium text-white px-5 py-2 rounded-full overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/25"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-500 transition-all duration-300" />
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <span className="relative flex items-center gap-1.5">
                  Get Started
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </span>
              </Link>
            </SignedOut>
            <SignedIn>
              <Link
                href="/dashboard"
                className="text-sm font-medium bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white px-5 py-2 rounded-full transition-all duration-300 shadow-lg shadow-indigo-600/20 hover:shadow-indigo-500/30"
              >
                Dashboard
              </Link>
              <UserButton />
            </SignedIn>
          </div>
        </div>
      </div>
    </nav>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
  accent,
  glowColor,
}: {
  icon: any;
  title: string;
  description: string;
  accent: string;
  glowColor: string;
}) {
  return (
    <div className="group relative bg-white/[0.02] border border-white/[0.06] rounded-2xl p-7 hover:border-white/[0.12] transition-all duration-500 overflow-hidden">
      {/* hover glow */}
      <div
        className={`absolute -top-20 -right-20 w-48 h-48 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none ${glowColor}`}
      />
      <div className="relative z-10">
        <div
          className={`w-12 h-12 rounded-xl flex items-center justify-center border mb-5 transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg ${accent}`}
        >
          <Icon className="w-5 h-5" />
        </div>
        <h3 className="text-white font-semibold text-lg mb-2.5">{title}</h3>
        <p className="text-white/40 text-sm leading-relaxed">{description}</p>
      </div>
    </div>
  );
}

function StepCard({
  number,
  title,
  description,
  isLast = false,
}: {
  number: string;
  title: string;
  description: string;
  isLast?: boolean;
}) {
  return (
    <div className="relative flex gap-6">
      {/* vertical line connector */}
      {!isLast && (
        <div className="absolute left-5 top-12 bottom-0 w-px bg-gradient-to-b from-indigo-500/30 to-transparent" />
      )}
      <div className="shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-sm relative z-10 shadow-lg shadow-indigo-500/10">
        {number}
      </div>
      <div className="pb-8">
        <h4 className="text-white font-semibold text-lg mb-1.5">{title}</h4>
        <p className="text-white/35 text-sm leading-relaxed">{description}</p>
      </div>
    </div>
  );
}

/* ── page ──────────────────────────────────────────────────────────── */

export default function Home() {
  return (
    <>
      <div className="min-h-screen bg-[#06060a] text-white">
        <NavBar />

        {/* ═══════════════════════════════════════════════════════════════
            HERO  — scroll-animated 3D asset
        ═══════════════════════════════════════════════════════════════ */}
        <SplineHero>
          {/* badge */}
          <div className="inline-flex items-center gap-2 bg-white/[0.04] border border-white/[0.08] rounded-full px-4 py-1.5 mb-6 backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
            </span>
            <span className="text-xs text-white/50 font-medium">
              Now in Public Beta
            </span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.1] tracking-tight mb-6">
            Build APIs{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
              visually.
            </span>
            <br />
            Deploy{" "}
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              instantly.
            </span>
          </h1>

          <p className="text-base sm:text-lg text-white/40 max-w-xl mx-auto lg:mx-0 mb-8 leading-relaxed">
            SynthTeam is a visual workflow editor that lets you design,
            connect, and deploy production-ready API endpoints — no
            boilerplate, no YAML, just drag &amp; drop.
          </p>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center lg:justify-start">
            <SignedOut>
              <Link
                href="/sign-up"
                className="group inline-flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium px-7 py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-600/25 hover:shadow-indigo-500/40 hover:scale-[1.02]"
              >
                Start Building — It&apos;s Free
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link
                href="/sign-in"
                className="inline-flex items-center justify-center gap-2 bg-white/[0.05] hover:bg-white/[0.08] border border-white/[0.08] text-white/70 hover:text-white font-medium px-7 py-3.5 rounded-xl transition-all hover:scale-[1.02]"
              >
                Sign In
              </Link>
            </SignedOut>
            <SignedIn>
              <Link
                href="/dashboard"
                className="group inline-flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium px-7 py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-600/25 hover:shadow-indigo-500/40 hover:scale-[1.02]"
              >
                Go to Dashboard
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </SignedIn>
          </div>

          {/* social proof line */}
          <div className="mt-10 flex items-center gap-3 justify-center lg:justify-start text-white/20 text-xs">
            <div className="flex -space-x-2">
              {[
                "bg-indigo-500",
                "bg-violet-500",
                "bg-cyan-500",
                "bg-emerald-500",
              ].map((c, i) => (
                <div
                  key={i}
                  className={`w-6 h-6 rounded-full ${c} border-2 border-[#06060a]`}
                />
              ))}
            </div>
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-3 h-3 text-amber-400 fill-amber-400" />
              ))}
            </div>
            <span>Trusted by 800+ developers worldwide</span>
          </div>
        </SplineHero>

        {/* ═══════════════════════════════════════════════════════════════
            MARQUEE — logos / trust bar (animated infinite scroll)
        ═══════════════════════════════════════════════════════════════ */}
        <section className="relative border-y border-white/[0.04] py-5 overflow-hidden">
          {/* edge fades */}
          <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-[#06060a] to-transparent z-10 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-[#06060a] to-transparent z-10 pointer-events-none" />

          <div className="marquee-track flex gap-16 text-white/20 text-sm font-medium whitespace-nowrap">
            {/* double the items for seamless loop */}
            {[...Array(2)].map((_, setIdx) => (
              <div key={setIdx} className="flex items-center gap-16 shrink-0">
                {[
                  { icon: Code2, label: "FastAPI" },
                  { icon: Globe, label: "Next.js" },
                  { icon: Layers, label: "PostgreSQL" },
                  { icon: Zap, label: "Redis" },
                  { icon: Cpu, label: "Docker" },
                  { icon: Shield, label: "Clerk" },
                  { icon: Sparkles, label: "React Flow" },
                  { icon: Rocket, label: "Swagger" },
                ].map(({ icon: I, label }) => (
                  <span key={`${setIdx}-${label}`} className="flex items-center gap-2.5 tracking-wide">
                    <I className="w-4 h-4 opacity-50" />
                    {label}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════════
            FEATURES
        ═══════════════════════════════════════════════════════════════ */}
        <section id="features" className="py-28 md:py-36 relative">
          {/* background accents */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-indigo-600/[0.03] rounded-full blur-[120px] pointer-events-none" />

          <div className="max-w-7xl mx-auto px-6 relative">
            <ScrollReveal>
              <div className="text-center mb-20">
                <div className="inline-flex items-center gap-2 bg-indigo-500/[0.08] border border-indigo-500/20 rounded-full px-4 py-1.5 mb-5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  <span className="text-xs text-indigo-400 font-semibold uppercase tracking-wider">
                    Features
                  </span>
                </div>
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-5">
                  Everything you need to
                  <br />
                  <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
                    ship APIs fast
                  </span>
                </h2>
                <p className="text-white/35 max-w-2xl mx-auto text-lg">
                  From visual design to one-click deployment, SynthTeam gives you
                  the complete toolkit for building robust API workflows.
                </p>
              </div>
            </ScrollReveal>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              <ScrollReveal delay={0}>
                <FeatureCard
                  icon={Layers}
                  title="Visual Flow Editor"
                  description="Drag-and-drop nodes, connect them visually, and define request/response schemas — all in a beautiful dark canvas."
                  accent="bg-indigo-500/15 text-indigo-400 border-indigo-500/25"
                  glowColor="bg-indigo-500/20"
                />
              </ScrollReveal>
              <ScrollReveal delay={100}>
                <FeatureCard
                  icon={Rocket}
                  title="One-Click Deploy"
                  description="Deploy your workflow as a live API endpoint instantly. Toggle flows on and off without touching any infrastructure."
                  accent="bg-violet-500/15 text-violet-400 border-violet-500/25"
                  glowColor="bg-violet-500/20"
                />
              </ScrollReveal>
              <ScrollReveal delay={200}>
                <FeatureCard
                  icon={Globe}
                  title="Live Swagger Docs"
                  description="Every deployed flow is auto-documented under its project namespace in /docs — ready for your team to consume."
                  accent="bg-cyan-500/15 text-cyan-400 border-cyan-500/25"
                  glowColor="bg-cyan-500/20"
                />
              </ScrollReveal>
              <ScrollReveal delay={100}>
                <FeatureCard
                  icon={Shield}
                  title="Secure by Default"
                  description="JWT-authenticated endpoints with Clerk, JWKS key rotation, and per-user project isolation out of the box."
                  accent="bg-emerald-500/15 text-emerald-400 border-emerald-500/25"
                  glowColor="bg-emerald-500/20"
                />
              </ScrollReveal>
              <ScrollReveal delay={200}>
                <FeatureCard
                  icon={Cpu}
                  title="Processor Pipeline"
                  description="Chain processors to transform, validate, and route data through your pipeline before the response is built."
                  accent="bg-amber-500/15 text-amber-400 border-amber-500/25"
                  glowColor="bg-amber-500/20"
                />
              </ScrollReveal>
              <ScrollReveal delay={300}>
                <FeatureCard
                  icon={Zap}
                  title="Real-time Hot Reload"
                  description="Edit nodes, save, and redeploy — changes go live in seconds. No server restarts, no downtime."
                  accent="bg-rose-500/15 text-rose-400 border-rose-500/25"
                  glowColor="bg-rose-500/20"
                />
              </ScrollReveal>
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════════
            HOW IT WORKS
        ═══════════════════════════════════════════════════════════════ */}
        <section id="how" className="py-28 md:py-36 relative border-t border-white/[0.04]">
          <div className="absolute top-1/4 right-0 w-[400px] h-[400px] bg-violet-600/[0.04] rounded-full blur-[100px] pointer-events-none" />

          <div className="max-w-7xl mx-auto px-6">
            <div className="grid lg:grid-cols-2 gap-20 items-center">
              {/* left — steps */}
              <ScrollReveal>
                <div>
                  <div className="inline-flex items-center gap-2 bg-violet-500/[0.08] border border-violet-500/20 rounded-full px-4 py-1.5 mb-5">
                    <Code2 className="w-3.5 h-3.5 text-violet-400" />
                    <span className="text-xs text-violet-400 font-semibold uppercase tracking-wider">
                      How it works
                    </span>
                  </div>
                  <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-12">
                    Three steps to a
                    <br />
                    <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
                      live API endpoint
                    </span>
                  </h2>

                  <div>
                    <StepCard
                      number="1"
                      title="Design your flow"
                      description="Add an HTTP Entry node, set the method and path, and define your request & response schemas."
                    />
                    <StepCard
                      number="2"
                      title="Connect processors"
                      description="Chain Processor nodes to transform data. Wire them up visually — no code required."
                    />
                    <StepCard
                      number="3"
                      title="Deploy & go live"
                      description="Hit Deploy. Your endpoint appears instantly in the Swagger docs, ready to receive traffic."
                      isLast
                    />
                  </div>
                </div>
              </ScrollReveal>

              {/* right — decorative code preview */}
              <ScrollReveal delay={200}>
                <div className="relative">
                  <div className="bg-[#0c0c15] border border-white/[0.06] rounded-2xl overflow-hidden shadow-2xl shadow-black/50">
                    {/* window chrome */}
                    <div className="flex items-center gap-2 px-5 py-3.5 border-b border-white/[0.06] bg-white/[0.02]">
                      <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                      <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
                      <div className="w-3 h-3 rounded-full bg-[#28c840]" />
                      <span className="ml-3 text-xs text-white/25 font-mono">
                        ~ / terminal
                      </span>
                    </div>

                    <div className="p-6 font-mono text-sm">
                      <div className="space-y-2 text-xs leading-relaxed">
                        <p>
                          <span className="text-emerald-400">❯</span>{" "}
                          <span className="text-white/70">
                            curl -X POST http://localhost:8000/greet
                          </span>
                        </p>
                        <p className="pl-4">
                          <span className="text-white/30">
                            -H &quot;Content-Type: application/json&quot;
                          </span>
                        </p>
                        <p className="pl-4">
                          <span className="text-white/30">
                            -d &apos;&#123;&quot;name&quot;: &quot;World&quot;&#125;&apos;
                          </span>
                        </p>
                        <div className="h-px bg-white/[0.06] my-4" />
                        <div className="bg-white/[0.03] rounded-lg p-4 border border-white/[0.04]">
                          <p className="text-indigo-400">
                            &#123;
                          </p>
                          <p className="text-white/60 pl-4">
                            &quot;message&quot;:{" "}
                            <span className="text-emerald-400">
                              &quot;Hello, World!&quot;
                            </span>
                            ,
                          </p>
                          <p className="text-white/60 pl-4">
                            &quot;status&quot;:{" "}
                            <span className="text-amber-400">200</span>,
                          </p>
                          <p className="text-white/60 pl-4">
                            &quot;timestamp&quot;:{" "}
                            <span className="text-cyan-400">
                              &quot;2026-02-18T12:00:00Z&quot;
                            </span>
                          </p>
                          <p className="text-indigo-400">&#125;</p>
                        </div>
                        <p className="mt-3">
                          <span className="text-emerald-400">❯</span>{" "}
                          <span className="text-white/20 animate-pulse">▌</span>
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* glow behind card */}
                  <div className="absolute -inset-6 bg-indigo-600/[0.05] rounded-3xl blur-3xl -z-10" />
                  <div className="absolute -inset-2 bg-violet-600/[0.03] rounded-3xl blur-2xl -z-10" />
                </div>
              </ScrollReveal>
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════════
            STATS BAR
        ═══════════════════════════════════════════════════════════════ */}
        <section className="border-y border-white/[0.04]">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-white/[0.04]">
              {[
                { value: "800+", label: "Active developers" },
                { value: "50ms", label: "Avg. response time" },
                { value: "99.9%", label: "Uptime SLA" },
                { value: "24/7", label: "Community support" },
              ].map(({ value, label }) => (
                <ScrollReveal key={label}>
                  <div className="py-10 text-center">
                    <div className="text-3xl sm:text-4xl font-bold bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent mb-2">
                      {value}
                    </div>
                    <div className="text-sm text-white/30">{label}</div>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════════
            CTA
        ═══════════════════════════════════════════════════════════════ */}
        <section id="cta" className="py-28 md:py-36 relative">
          <div className="max-w-4xl mx-auto px-6 relative">
            {/* animated glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-indigo-600/[0.08] rounded-full blur-[120px] pointer-events-none animate-pulse" />
            <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-[300px] h-[300px] bg-violet-600/[0.06] rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute top-1/2 right-1/4 -translate-y-1/2 w-[300px] h-[300px] bg-purple-600/[0.05] rounded-full blur-[100px] pointer-events-none" />

            <ScrollReveal>
              <div className="relative text-center">
                {/* bordered card with gradient border */}
                <div className="relative rounded-3xl overflow-hidden">
                  {/* gradient border effect */}
                  <div className="absolute inset-0 rounded-3xl bg-gradient-to-b from-white/[0.08] via-indigo-500/20 to-white/[0.04] p-px">
                    <div className="w-full h-full rounded-3xl bg-[#0a0a12]" />
                  </div>

                  <div className="relative py-16 sm:py-20 px-8">
                    <div className="inline-flex items-center gap-2 bg-indigo-500/[0.08] border border-indigo-500/20 rounded-full px-4 py-1.5 mb-6">
                      <Rocket className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="text-xs text-indigo-400 font-semibold uppercase tracking-wider">
                        Get Started
                      </span>
                    </div>

                    <h2 className="text-3xl sm:text-5xl font-bold tracking-tight mb-6">
                      Ready to build your
                      <br />
                      <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
                        next API?
                      </span>
                    </h2>
                    <p className="text-white/35 max-w-lg mx-auto mb-10 text-lg">
                      Join hundreds of developers who ship APIs faster with SynthTeam.
                      Free to start — no credit card required.
                    </p>

                    <SignedOut>
                      <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link
                          href="/sign-up"
                          className="group inline-flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium px-8 py-4 rounded-xl transition-all duration-300 shadow-lg shadow-indigo-600/25 hover:shadow-indigo-500/40 hover:scale-[1.02] text-base"
                        >
                          Get Started for Free
                          <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                        </Link>
                        <a
                          href="https://github.com"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group inline-flex items-center justify-center gap-2 bg-white/[0.05] hover:bg-white/[0.08] border border-white/[0.08] text-white/60 hover:text-white font-medium px-8 py-4 rounded-xl transition-all duration-300 text-base"
                        >
                          <Github className="w-4 h-4" />
                          Star on GitHub
                        </a>
                      </div>
                    </SignedOut>
                    <SignedIn>
                      <Link
                        href="/dashboard"
                        className="group inline-flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium px-8 py-4 rounded-xl transition-all duration-300 shadow-lg shadow-indigo-600/25 hover:shadow-indigo-500/40 hover:scale-[1.02] text-base"
                      >
                        Open Dashboard
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                      </Link>
                    </SignedIn>
                  </div>
                </div>
              </div>
            </ScrollReveal>
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════════
            FOOTER
        ═══════════════════════════════════════════════════════════════ */}
        <footer className="border-t border-white/[0.04]">
          <div className="max-w-7xl mx-auto px-6">
            {/* main footer grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 py-16">
              {/* brand */}
              <div className="col-span-2 md:col-span-1">
                <Link href="/" className="flex items-center gap-2.5 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
                    <Zap className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-lg font-bold text-white">
                    Synth<span className="text-indigo-400">Team</span>
                  </span>
                </Link>
                <p className="text-white/25 text-sm leading-relaxed max-w-xs">
                  Visual API builder for modern developers.
                  Design, connect, and deploy — all from your browser.
                </p>
              </div>

              {/* product */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-white/50 mb-4">Product</h4>
                <ul className="space-y-2.5">
                  {["Features", "Pricing", "Changelog", "Roadmap"].map((item) => (
                    <li key={item}>
                      <a href="#" className="text-sm text-white/25 hover:text-white/60 transition-colors flex items-center gap-1 group">
                        <ChevronRight className="w-3 h-3 text-white/10 group-hover:text-white/30 transition-colors" />
                        {item}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>

              {/* resources */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-white/50 mb-4">Resources</h4>
                <ul className="space-y-2.5">
                  {["Documentation", "API Reference", "Guides", "Blog"].map((item) => (
                    <li key={item}>
                      <a href="#" className="text-sm text-white/25 hover:text-white/60 transition-colors flex items-center gap-1 group">
                        <ChevronRight className="w-3 h-3 text-white/10 group-hover:text-white/30 transition-colors" />
                        {item}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>

              {/* company */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-white/50 mb-4">Company</h4>
                <ul className="space-y-2.5">
                  {["About", "Careers", "Privacy Policy", "Terms of Service"].map((item) => (
                    <li key={item}>
                      <a href="#" className="text-sm text-white/25 hover:text-white/60 transition-colors flex items-center gap-1 group">
                        <ChevronRight className="w-3 h-3 text-white/10 group-hover:text-white/30 transition-colors" />
                        {item}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* bottom bar */}
            <div className="border-t border-white/[0.04] py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
              <p className="text-xs text-white/20">
                &copy; {new Date().getFullYear()} SynthTeam. All rights reserved.
              </p>
              <div className="flex items-center gap-4">
                <a href="#" className="text-white/20 hover:text-white/50 transition-colors">
                  <Github className="w-4 h-4" />
                </a>
                <a href="#" className="text-white/20 hover:text-white/50 transition-colors">
                  <Twitter className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
