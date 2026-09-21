import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import {
  ShieldAlert,
  SlidersHorizontal,
  FileCheck2,
  Cpu,
  History,
  FlaskConical,
  Scale,
  Sparkles,
} from "lucide-react";

export const metadata: Metadata = {
  title: "LedgerOS | Autonomous Finance Controller & Revenue Recovery",
  description: "Enterprise autonomous finance ops platform built on FinRCA-Bench and Razorpay.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col antialiased">
        {/* Top Header */}
        <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-[#070b14]/80 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
                <Scale className="h-5 w-5 text-white" />
              </div>
              <div>
                <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  LEDGER<span className="text-blue-500">OS</span>
                </span>
                <span className="block text-[10px] uppercase font-mono tracking-widest text-slate-400 -mt-1">
                  Autonomous Finance Controller
                </span>
              </div>
            </Link>

            <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
              <Link
                href="/"
                className="px-3 py-1.5 rounded-md hover:bg-slate-800/60 hover:text-white text-slate-300 transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/investigations"
                className="px-3 py-1.5 rounded-md hover:bg-slate-800/60 hover:text-white text-slate-300 transition-colors flex items-center gap-1.5"
              >
                <Cpu className="h-3.5 w-3.5 text-blue-400" />
                Investigations
              </Link>
              <Link
                href="/reconciliation"
                className="px-3 py-1.5 rounded-md hover:bg-slate-800/60 hover:text-white text-slate-300 transition-colors"
              >
                Reconciliation
              </Link>
              <Link
                href="/approvals"
                className="px-3 py-1.5 rounded-md hover:bg-slate-800/60 hover:text-white text-slate-300 transition-colors flex items-center gap-1.5"
              >
                <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
                Approvals
              </Link>
              <Link
                href="/audit"
                className="px-3 py-1.5 rounded-md hover:bg-slate-800/60 hover:text-white text-slate-300 transition-colors flex items-center gap-1.5"
              >
                <History className="h-3.5 w-3.5 text-emerald-400" />
                Audit Trail
              </Link>
              <Link
                href="/evaluations"
                className="px-3 py-1.5 rounded-md hover:bg-slate-800/60 hover:text-white text-slate-300 transition-colors flex items-center gap-1.5"
              >
                <FlaskConical className="h-3.5 w-3.5 text-indigo-400" />
                Evaluation Lab
              </Link>
              <Link
                href="/control-room"
                className="px-3 py-1.5 rounded-md hover:bg-slate-800/60 hover:text-white text-slate-300 transition-colors flex items-center gap-1.5 text-blue-400 font-semibold"
              >
                <SlidersHorizontal className="h-3.5 w-3.5 text-blue-400" />
                Control Room
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/50 text-emerald-400 text-xs font-mono">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Razorpay Test & FinRCA Live
            </div>
          </div>
        </header>

        {/* Main Workspace */}
        <main className="flex-1 max-w-7xl w-full mx-auto p-6">{children}</main>

        <footer className="border-t border-slate-900 bg-[#070b14] px-6 py-4 text-center text-xs text-slate-500 font-mono">
          LedgerOS &bull; Autonomous Finance Operations &bull; Grounded on public FinRCA-Bench research benchmark &amp; Razorpay Payments
        </footer>
      </body>
    </html>
  );
}
