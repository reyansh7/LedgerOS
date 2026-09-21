"use client";

import { useEffect, useState } from "react";
import {
  Cpu,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Play,
  Share2,
  FileText,
  Building,
  CreditCard,
  Layers,
  ArrowRight,
} from "lucide-react";

interface ExceptionItem {
  case_id: string;
  failure_type: string;
  primary_entity_type: string;
  primary_entity_id: string;
  counterparty_id: string | null;
  amount_at_risk: number;
  currency: string;
  observed_symptom: string;
  status: string;
  severity: string;
  root_cause: string | null;
  created_at: string;
}

interface Milestone {
  step: string;
  status: string;
  detail: string;
  timestamp: string;
}

interface ExceptionDetail extends ExceptionItem {
  recommended_action: string | null;
  provenance_subgraph: {
    root_entity: string;
    evidence_count: number;
    nodes: Array<{
      entity_type: string;
      entity_id: string;
      data: any;
    }>;
    edges: Array<{
      source: string;
      target: string;
      relation: string;
    }>;
  };
}

export default function InvestigationsPage() {
  const [exceptions, setExceptions] = useState<ExceptionItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ExceptionDetail | null>(null);
  const [investigating, setInvestigating] = useState(false);
  const [liveMilestones, setLiveMilestones] = useState<Milestone[]>([]);

  useEffect(() => {
    fetch("/api/exceptions?limit=50")
      .then((res) => res.json())
      .then((data) => {
        setExceptions(data);
        if (data.length > 0) {
          setSelectedCaseId(data[0].case_id);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedCaseId) return;
    setDetail(null);
    setLiveMilestones([]);
    fetch(`/api/exceptions/${selectedCaseId}`)
      .then((res) => res.json())
      .then((data) => setDetail(data))
      .catch(console.error);
  }, [selectedCaseId]);

  const handleStartInvestigation = async () => {
    if (!selectedCaseId) return;
    setInvestigating(true);
    setLiveMilestones([]);

    try {
      const res = await fetch(`/api/investigations/${selectedCaseId}/start`, { method: "POST" });
      const data = await res.json();
      setLiveMilestones(data.activity_log || []);
      // Refresh detail
      const dRes = await fetch(`/api/exceptions/${selectedCaseId}`);
      const dData = await dRes.json();
      setDetail(dData);
    } catch (e) {
      console.error(e);
    } finally {
      setInvestigating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Cpu className="h-6 w-6 text-blue-500" />
          Financial Detective &amp; Agent Lab
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Autonomous causal investigation over typed provenance graphs with policy-bounded action planning.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Exception Queue */}
        <div className="lg:col-span-5 rounded-xl bg-slate-900/60 border border-slate-800 p-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs font-mono text-slate-400">
            <span>DISCREPANCY CASES ({exceptions.length})</span>
            <span>SORT: SEVERITY</span>
          </div>

          <div className="mt-3 space-y-2 max-h-[700px] overflow-y-auto pr-1">
            {exceptions.map((exc) => {
              const isSelected = exc.case_id === selectedCaseId;
              return (
                <div
                  key={exc.case_id}
                  onClick={() => setSelectedCaseId(exc.case_id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? "bg-blue-950/30 border-blue-500/50 shadow-md shadow-blue-500/10"
                      : "bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-semibold text-blue-400">{exc.case_id}</span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase font-semibold ${
                        exc.severity === "critical"
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                          : exc.severity === "high"
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                      }`}
                    >
                      {exc.severity}
                    </span>
                  </div>

                  <div className="text-xs font-medium text-slate-200 mt-1">{exc.failure_type}</div>

                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{exc.observed_symptom}</p>

                  <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span>
                      At Risk: <strong className="text-white">₹{exc.amount_at_risk.toLocaleString()}</strong>
                    </span>
                    <span className="capitalize">{exc.status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Case Deep Dive & Agent Live Milestones */}
        <div className="lg:col-span-7 space-y-6">
          {detail ? (
            <>
              {/* Case Header Card */}
              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-mono text-blue-400">{detail.case_id}</span>
                    <h2 className="text-lg font-bold text-white mt-0.5">{detail.failure_type}</h2>
                    <p className="text-xs text-slate-300 mt-1">{detail.observed_symptom}</p>
                  </div>

                  <button
                    onClick={handleStartInvestigation}
                    disabled={investigating}
                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs font-semibold shadow-lg shadow-blue-600/20 hover:from-blue-500 hover:to-indigo-500 transition flex items-center gap-2 disabled:opacity-50 shrink-0"
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    {investigating ? "Investigating..." : "Launch LangGraph Agent"}
                  </button>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-3 pt-4 border-t border-slate-800 text-xs font-mono">
                  <div>
                    <span className="text-slate-500 block">Primary Entity:</span>
                    <span className="text-slate-200">
                      {detail.primary_entity_type}:{detail.primary_entity_id}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Counterparty:</span>
                    <span className="text-slate-200">{detail.counterparty_id || "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Amount At Risk:</span>
                    <span className="text-rose-400 font-bold">₹{detail.amount_at_risk.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* LIVE AGENT ACTIVITY MILESTONES */}
              {liveMilestones.length > 0 && (
                <div className="p-5 rounded-xl bg-slate-900/60 border border-blue-500/30 bg-blue-950/10">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-blue-400 uppercase tracking-wider mb-3">
                    <CheckCircle2 className="h-4 w-4 text-blue-400" />
                    Agent Activity Milestones (Explainable Trace)
                  </div>
                  <div className="space-y-2.5 font-mono text-xs">
                    {liveMilestones.map((m, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-slate-200">
                        <span className="text-emerald-400 font-bold">✓</span>
                        <div>
                          <strong className="text-slate-300">{m.step}:</strong>{" "}
                          <span className="text-slate-400">{m.detail}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Typed Provenance Graph Cards */}
              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Share2 className="h-4 w-4 text-indigo-400" />
                    <h3 className="text-xs font-mono uppercase tracking-wider font-semibold text-slate-200">
                      Typed Provenance Subgraph ({detail.provenance_subgraph?.evidence_count || 0} Relational Nodes)
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-indigo-400">Schema-Traversed</span>
                </div>

                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {detail.provenance_subgraph?.nodes?.slice(0, 6).map((node, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs font-mono"
                    >
                      <div className="flex items-center justify-between text-slate-400">
                        <span className="uppercase text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                          {node.entity_type}
                        </span>
                        <span className="text-blue-400 font-semibold">{node.entity_id}</span>
                      </div>
                      <div className="mt-2 text-[11px] text-slate-400 space-y-0.5">
                        {Object.entries(node.data)
                          .filter(([k]) => !k.includes("id") && typeof node.data[k] !== "object")
                          .slice(0, 3)
                          .map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                              <span className="text-slate-500 capitalize">{k.replace("_", " ")}:</span>
                              <span className="text-slate-300">{String(v)}</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-sm text-slate-500">
              Select an exception to inspect causal evidence and launch investigation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
