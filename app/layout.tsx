import "./globals.css";
import type { Metadata } from "next";
import { Nav } from "./components/Nav";
import { SampleDataBanner } from "./components/SampleDataBanner";

export const metadata: Metadata = {
  title: "WC26 Predictor — FIFA World Cup 2026 forecasts",
  description:
    "Calibrated probabilistic predictions for FIFA World Cup 2026 matches, with Monte Carlo tournament simulation. Probabilistic estimates, not betting advice.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen font-sans">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded-lg focus:bg-gold-500 focus:text-black focus:px-3 focus:py-1.5 focus:text-sm focus:text-white"
        >
          Skip to content
        </a>

        {/* Ambient tournament backdrop: faint grid + colour wash */}
        <div className="pointer-events-none fixed inset-0 -z-10">
          <div className="absolute inset-0 bg-grid-faint bg-grid opacity-30" />
          <div className="absolute -top-40 left-1/4 h-[40rem] w-[60rem] -translate-x-1/2 rounded-full bg-crimson-700/12 blur-[140px]" />
          <div className="absolute -top-20 right-0 h-[36rem] w-[60rem] translate-x-1/3 rounded-full bg-gold-500/10 blur-[160px]" />
          <div className="absolute bottom-[-22rem] left-1/3 h-[36rem] w-[60rem] -translate-x-1/2 rounded-full bg-pitch-700/12 blur-[140px]" />
        </div>

        <Nav />
        <SampleDataBanner />

        <main id="main" className="mx-auto max-w-6xl px-4 py-6">
          {children}
        </main>

        <footer className="mx-auto max-w-6xl px-4 py-10 text-xs text-muted">
          <div className="divider mb-6" />
          Forecasts are probability estimates from a statistical model. They are not guarantees and
          not betting advice.
        </footer>
      </body>
    </html>
  );
}
