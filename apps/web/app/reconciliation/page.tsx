"use client";

import { useEffect, useState } from "react";
import { CheckCircle, AlertCircle, RefreshCw, FileText, ArrowRightLeft } from "lucide-react";

interface MatchRecord {
  match_id: string;
  run_id: string;
  match_type: string;
  entity1: string;
  entity2: string;
  amount1: number;
  amount2: number;
  variance: number;
  confidence: number;
  matched_at: string;
}

export default function ReconciliationPage() {
  const [matches, setMatches] = useState<MatchRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMatches = () => {
    fetch("/api/reconciliation/matches?limit=100")
      .then((res) => res.json())
      .then((data) => setMatches(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchMatches();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <ArrowRightLeft className="h-6 w-6 text-emerald-400" />
            3-Way Reconciliation Matrix
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Deterministic multi-stage matching across Purchase Orders, Invoices, ERP Disbursements, Bank Statements, and General Ledger.
          </p>
        </div>

        <button
          onClick={fetchMatches}
          className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:bg-slate-800 transition flex items-center gap-1.5 self-start"
        >
          <RefreshCw className="h-3 w-3" /> Refresh Matches
        </button>
      </div>

      {/* Reconciliation Matches Table */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between font-mono text-xs text-slate-400">
          <span>MATCHED TRANSACTION PAIRS ({matches.length})</span>
          <span>DETERMINISTIC CONFIDENCE: 98% - 100%</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider border-b border-slate-800 text-[11px]">
              <tr>
                <th className="p-3.5">Match ID</th>
                <th className="p-3.5">Type</th>
                <th className="p-3.5">Source Entity 1</th>
                <th className="p-3.5">Target Entity 2</th>
                <th className="p-3.5">Amount 1</th>
                <th className="p-3.5">Amount 2</th>
                <th className="p-3.5">Variance</th>
                <th className="p-3.5">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {matches.map((m) => (
                <tr key={m.match_id} className="hover:bg-slate-800/30 transition">
                  <td className="p-3.5 font-semibold text-blue-400">{m.match_id}</td>
                  <td className="p-3.5">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                      {m.match_type}
                    </span>
                  </td>
                  <td className="p-3.5 text-slate-200">{m.entity1}</td>
                  <td className="p-3.5 text-slate-200">{m.entity2}</td>
                  <td className="p-3.5">₹{m.amount1.toLocaleString()}</td>
                  <td className="p-3.5">₹{m.amount2.toLocaleString()}</td>
                  <td className="p-3.5 text-emerald-400">
                    {m.variance === 0 ? "₹0.00" : `₹${m.variance.toLocaleString()}`}
                  </td>
                  <td className="p-3.5 text-emerald-400 font-semibold">
                    {(m.confidence * 100).toFixed(0)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
