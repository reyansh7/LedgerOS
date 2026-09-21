"use client";

import { useEffect, useState } from "react";
import { FlaskConical, Play, CheckCircle2, AlertCircle, BarChart3, ShieldCheck } from "lucide-react";

interface BenchmarkMetrics {
  benchmark_ground_truth_total: number;
  true_positives_detected: number;
  false_negatives: number;
  false_positives: number;
  detection_recall_pct: number;
  detection_precision_pct: number;
  detection_f1_score: number;
  match_rate_pct: number;
  false_reconciliation_rate_pct: number;
  category_accuracy_pct: number;
  run_id?: string;
  evaluated_split: string;
  evaluated_subset_name?: string;
  total_exceptions_in_db: number;
  total_matches_in_db: number;
  ground_truth_by_category?: Record<string, number>;
  detected_by_category?: Record<string, number>;
}

export default function EvaluationsPage() {
  const [metrics, setMetrics] = useState<BenchmarkMetrics | null>(null);
  const [running, setRunning] = useState(false);
  const [split, setSplit] = useState<string>("");

  const runEvaluation = async (selectedSplit = split) => {
    setRunning(true);
    try {
      const url = selectedSplit ? `/api/evaluations/run?split=${selectedSplit}` : `/api/evaluations/run`;
      const res = await fetch(url);
      const data = await res.json();
      setMetrics(data);
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    runEvaluation();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <FlaskConical className="h-6 w-6 text-indigo-400" />
              Evaluation Lab &amp; Objective Benchmark
            </h1>
            {metrics?.run_id && (
              <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-xs border border-indigo-500/30">
                {metrics.run_id}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-0.5">
            Rigorous evaluation against public FinRCA-Bench ground truth. <span className="text-slate-300 font-semibold">{metrics?.evaluated_subset_name || "LedgerOS Evaluation Subset: 50 Cases"}</span> with strictly isolated evaluator metrics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={split}
            onChange={(e) => {
              setSplit(e.target.value);
              runEvaluation(e.target.value);
            }}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 font-mono"
          >
            <option value="">LedgerOS Evaluation Subset: 50 Cases (All Splits)</option>
            <option value="train">Train Split</option>
            <option value="validation">Validation Split</option>
            <option value="test">Test Split</option>
          </select>

          <button
            onClick={() => runEvaluation()}
            disabled={running}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition flex items-center gap-1.5 disabled:opacity-50"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            {running ? "Grading..." : "Re-run Benchmark"}
          </button>
        </div>
      </div>

      {metrics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs font-mono uppercase text-slate-400">Detection Recall</div>
            <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">
              {metrics.detection_recall_pct}%
            </div>
            <div className="mt-1 text-xs text-slate-500 font-mono">
              {metrics.true_positives_detected} of {metrics.benchmark_ground_truth_total} ground truth failures
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs font-mono uppercase text-slate-400">Reconciliation Match Rate</div>
            <div className="mt-2 text-2xl font-bold text-blue-400 font-mono">
              {metrics.match_rate_pct}%
            </div>
            <div className="mt-1 text-xs text-slate-500 font-mono">
              {metrics.total_matches_in_db} clean pairs matched
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs font-mono uppercase text-slate-400">False Reconciliation Rate</div>
            <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">
              {metrics.false_reconciliation_rate_pct}%
            </div>
            <div className="mt-1 text-xs text-slate-500 font-mono">
              Target &lt; 0.05% (Zero fabrication)
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-xs font-mono uppercase text-slate-400">Category Accuracy</div>
            <div className="mt-2 text-2xl font-bold text-indigo-400 font-mono">
              {metrics.category_accuracy_pct}%
            </div>
            <div className="mt-1 text-xs text-slate-500 font-mono">
              RCA classification precision
            </div>
          </div>
        </div>
      )}

      {/* Ground Truth Isolation Notice */}
      <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono text-slate-400 flex items-start gap-3">
        <ShieldCheck className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-200">Architectural Firewall Active:</strong> Ground-truth labels, causal edges, and mutation logs are quarantined in the evaluator repository. Agents operate strictly on model-visible operational tables (invoices, payments, bank records), guaranteeing uncompromised evaluation rigor.
        </div>
      </div>
    </div>
  );
}
