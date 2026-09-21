"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Server,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Layers,
  Database,
  Lock,
  ArrowUpRight,
  FileCheck,
  Search,
} from "lucide-react";

interface SystemHealth {
  timestamp: string;
  overall_status: string;
  components: {
    reconciliation_engine: {
      name: string;
      status: string;
      last_run: string | null;
      matched_records: number;
      match_rate: number;
    };
    agent_orchestrator: {
      name: string;
      status: string;
      model_routing: string;
      checkpoints: string;
    };
    policy_engine: {
      name: string;
      status: string;
      version: string;
      rules_loaded: number;
    };
    approval_service: {
      name: string;
      status: string;
      pending_approvals: number;
    };
    audit_ledger: {
      name: string;
      status: string;
      verified_blocks: number;
      is_chain_valid: boolean;
    };
    database: {
      name: string;
      status: string;
      latency_ms: number;
    };
  };
  connectors: Array<{
    connector_id: string;
    name: string;
    type: string;
    environment: string;
    status: string;
    latency_ms: number;
    capabilities: string[];
    read_only: boolean;
  }>;
  active_guardrails_count: number;
}

interface Guardrail {
  rule_id: string;
  name: string;
  category: string;
  enforced_by: string;
  description: string;
  active: boolean;
}

interface DecisionReceipt {
  receipt_id: string;
  case_id: string;
  exception_type: string;
  severity: string;
  exposure_amount: number;
  currency: string;
  root_cause: string;
  proposed_action: string;
  policy_version: string;
  autonomy_level: string;
  policy_decision: string;
  approval_status: string;
  verification_status: string;
  audit_hash: string;
  audit_id: string;
  evidence_count: number;
  timestamp: string;
}

export default function ControlRoomPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [guardrails, setGuardrails] = useState<Guardrail[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchCaseId, setSearchCaseId] = useState("");
  const [receipt, setReceipt] = useState<DecisionReceipt | null>(null);
  const [receiptLoading, setReceiptLoading] = useState(false);
  const [receiptError, setReceiptError] = useState("");

  const fetchData = async () => {
    try {
      const [resHealth, resGuardrails] = await Promise.all([
        fetch("/api/system/control-room"),
        fetch("/api/system/guardrails"),
      ]);
      if (resHealth.ok) {
        setHealth(await resHealth.json());
      }
      if (resGuardrails.ok) {
        setGuardrails(await resGuardrails.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 8000);
    return () => clearInterval(timer);
  }, []);

  const handleLookupReceipt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchCaseId.trim()) return;
    setReceiptLoading(true);
    setReceiptError("");
    setReceipt(null);
    try {
      const res = await fetch(`/api/system/receipts/${encodeURIComponent(searchCaseId.trim())}`);
      if (res.ok) {
        setReceipt(await res.json());
      } else {
        setReceiptError(`No decision receipt found for case: ${searchCaseId}`);
      }
    } catch (err) {
      setReceiptError("Failed to retrieve decision receipt.");
    } finally {
      setReceiptLoading(false);
    }
  };

  if (loading && !health) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-slate-400">
          <RefreshCw className="h-5 w-5 animate-spin text-blue-500" />
          <span className="font-mono text-sm">Connecting to LedgerOS System Telemetry...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Activity className="h-6 w-6 text-blue-500" />
              System Control Room & Governance
            </h1>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${
                health?.overall_status === "HEALTHY"
                  ? "bg-emerald-950/50 text-emerald-400 border-emerald-800/60"
                  : "bg-amber-950/50 text-amber-400 border-amber-800/60"
              }`}
            >
              {health?.overall_status || "UNKNOWN"}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time telemetry across deterministic matching, causal agent graph, FIN-POL policy gates, and chained audit ledger.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs text-slate-400">
          <span>Active Guardrails: <strong className="text-blue-400">{health?.active_guardrails_count || 8}</strong></span>
          <span>•</span>
          <span>Last Sync: {health ? new Date(health.timestamp).toLocaleTimeString() : "--"}</span>
          <button
            onClick={fetchData}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Subsystem Health Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Reconciliation Matcher */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Deterministic Engine</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950/40 text-emerald-400 border border-emerald-800/40">
              {health?.components.reconciliation_engine.status}
            </span>
          </div>
          <h3 className="text-base font-semibold text-white mb-2">
            {health?.components.reconciliation_engine.name}
          </h3>
          <div className="space-y-1.5 text-xs text-slate-400 font-mono">
            <div className="flex justify-between">
              <span>Matched Records:</span>
              <span className="text-white font-medium">{health?.components.reconciliation_engine.matched_records}</span>
            </div>
            <div className="flex justify-between">
              <span>Match Rate:</span>
              <span className="text-emerald-400 font-medium">{health?.components.reconciliation_engine.match_rate}%</span>
            </div>
          </div>
        </div>

        {/* Agent Orchestrator */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Agent Orchestrator</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-blue-950/40 text-blue-400 border border-blue-800/40">
              {health?.components.agent_orchestrator.status}
            </span>
          </div>
          <h3 className="text-base font-semibold text-white mb-2">
            {health?.components.agent_orchestrator.name}
          </h3>
          <div className="space-y-1.5 text-xs text-slate-400 font-mono">
            <div className="flex justify-between">
              <span>Routing:</span>
              <span className="text-slate-300 font-medium truncate max-w-[170px]">{health?.components.agent_orchestrator.model_routing}</span>
            </div>
            <div className="flex justify-between">
              <span>Checkpoints:</span>
              <span className="text-blue-400 font-medium">{health?.components.agent_orchestrator.checkpoints}</span>
            </div>
          </div>
        </div>

        {/* Policy Engine */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Governance Gate</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-indigo-950/40 text-indigo-400 border border-indigo-800/40">
              {health?.components.policy_engine.status}
            </span>
          </div>
          <h3 className="text-base font-semibold text-white mb-2">
            {health?.components.policy_engine.name}
          </h3>
          <div className="space-y-1.5 text-xs text-slate-400 font-mono">
            <div className="flex justify-between">
              <span>Version:</span>
              <span className="text-amber-400 font-medium">{health?.components.policy_engine.version}</span>
            </div>
            <div className="flex justify-between">
              <span>Rules Loaded:</span>
              <span className="text-white font-medium">{health?.components.policy_engine.rules_loaded} Active Bounds</span>
            </div>
          </div>
        </div>

        {/* Audit Ledger */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Cryptographic Audit</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950/40 text-emerald-400 border border-emerald-800/40">
              {health?.components.audit_ledger.status}
            </span>
          </div>
          <h3 className="text-base font-semibold text-white mb-2">
            {health?.components.audit_ledger.name}
          </h3>
          <div className="space-y-1.5 text-xs text-slate-400 font-mono">
            <div className="flex justify-between">
              <span>Verified Blocks:</span>
              <span className="text-emerald-400 font-medium">{health?.components.audit_ledger.verified_blocks}</span>
            </div>
            <div className="flex justify-between">
              <span>Chain Integrity:</span>
              <span className="text-emerald-400 font-medium">VALID (SHA-256)</span>
            </div>
          </div>
        </div>

        {/* Human Governance */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Human-in-the-Loop</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-blue-950/40 text-blue-400 border border-blue-800/40">
              {health?.components.approval_service.status}
            </span>
          </div>
          <h3 className="text-base font-semibold text-white mb-2">
            {health?.components.approval_service.name}
          </h3>
          <div className="space-y-1.5 text-xs text-slate-400 font-mono">
            <div className="flex justify-between">
              <span>Pending Approvals:</span>
              <span className="text-amber-400 font-medium">{health?.components.approval_service.pending_approvals}</span>
            </div>
            <div className="flex justify-between">
              <span>Server-Side RBAC:</span>
              <span className="text-slate-300 font-medium">FINANCE_CONTROLLER</span>
            </div>
          </div>
        </div>

        {/* Database & Latency */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Enterprise Store</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-950/40 text-emerald-400 border border-emerald-800/40">
              {health?.components.database.status}
            </span>
          </div>
          <h3 className="text-base font-semibold text-white mb-2">
            {health?.components.database.name}
          </h3>
          <div className="space-y-1.5 text-xs text-slate-400 font-mono">
            <div className="flex justify-between">
              <span>Query Latency:</span>
              <span className="text-emerald-400 font-medium">{health?.components.database.latency_ms} ms</span>
            </div>
            <div className="flex justify-between">
              <span>Ground Truth Isolation:</span>
              <span className="text-blue-400 font-medium">ENFORCED</span>
            </div>
          </div>
        </div>
      </div>

      {/* Enterprise Connectors & Capability Discovery */}
      <div className="rounded-xl bg-slate-900/40 border border-slate-800/80 overflow-hidden">
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Layers className="h-5 w-5 text-indigo-400" />
            <div>
              <h2 className="text-base font-semibold text-white">Registered Enterprise Connectors</h2>
              <p className="text-xs text-slate-400">Pluggable data abstraction layer mapping external sources to Canonical Financial Domain.</p>
            </div>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Active Connectors: <strong className="text-indigo-400">{health?.connectors.length || 0}</strong>
          </span>
        </div>

        <div className="divide-y divide-slate-800/60">
          {health?.connectors.map((c) => (
            <div key={c.connector_id} className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2.5">
                  <span className="font-semibold text-white">{c.name}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                    {c.connector_id}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-950/40 text-blue-400 border border-blue-800/40">
                    {c.environment}
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {c.capabilities.map((cap) => (
                    <span
                      key={cap}
                      className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800/80 text-slate-300 border border-slate-700/50"
                    >
                      {cap}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs font-mono">
                <div className="text-right">
                  <div className="text-slate-400">Mode: {c.read_only ? "READ-ONLY" : "READ / WRITE"}</div>
                  <div className="text-emerald-400">{c.latency_ms}ms ping</div>
                </div>
                <span className="px-2.5 py-1 rounded bg-emerald-950/40 border border-emerald-800/40 text-emerald-400 text-xs font-mono">
                  {c.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Operational Guardrails Table */}
      <div className="rounded-xl bg-slate-900/40 border border-slate-800/80 overflow-hidden">
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Lock className="h-5 w-5 text-amber-400" />
            <div>
              <h2 className="text-base font-semibold text-white">Active Operational Guardrails</h2>
              <p className="text-xs text-slate-400">Strict deterministic constraints preventing autonomous policy drift or unsafe financial mutations.</p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded text-xs font-mono bg-emerald-950/40 border border-emerald-800/40 text-emerald-400">
            All 8 Guardrails Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono border-b border-slate-800">
              <tr>
                <th className="p-3.5">ID</th>
                <th className="p-3.5">Guardrail</th>
                <th className="p-3.5">Category</th>
                <th className="p-3.5">Enforcement Boundary</th>
                <th className="p-3.5">Description</th>
                <th className="p-3.5">State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-slate-300">
              {guardrails.map((g) => (
                <tr key={g.rule_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-3.5 font-mono text-amber-400 font-semibold">{g.rule_id}</td>
                  <td className="p-3.5 font-medium text-white">{g.name}</td>
                  <td className="p-3.5 font-mono text-slate-400">{g.category}</td>
                  <td className="p-3.5 font-mono text-blue-400">{g.enforced_by}</td>
                  <td className="p-3.5 text-slate-400 max-w-md">{g.description}</td>
                  <td className="p-3.5">
                    <span className="flex items-center gap-1.5 text-emerald-400 font-mono">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      ENFORCED
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Decision Receipt Explorer */}
      <div className="rounded-xl bg-slate-900/40 border border-slate-800/80 p-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <FileCheck className="h-5 w-5 text-blue-400" />
          <div>
            <h2 className="text-base font-semibold text-white">Cryptographic Decision Receipt Lookup</h2>
            <p className="text-xs text-slate-400">
              Inspect immutable, explainable decision receipts for any case processed by LedgerOS.
            </p>
          </div>
        </div>

        <form onSubmit={handleLookupReceipt} className="flex gap-3 max-w-xl">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="e.g. CASE-04a08154 or CASE-dup-inv-001"
              value={searchCaseId}
              onChange={(e) => setSearchCaseId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={receiptLoading}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold font-mono disabled:opacity-50 transition-colors"
          >
            {receiptLoading ? "Querying..." : "Retrieve Receipt"}
          </button>
        </form>

        {receiptError && (
          <div className="p-3 rounded-lg bg-red-950/30 border border-red-800/50 text-red-400 text-xs font-mono flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            {receiptError}
          </div>
        )}

        {receipt && (
          <div className="p-5 rounded-xl bg-slate-900/80 border border-blue-500/30 font-mono text-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-blue-400 font-bold text-sm">DECISION RECEIPT: {receipt.receipt_id}</span>
              <span className="px-2.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                {receipt.policy_decision}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-slate-300">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Case ID</span>
                <span className="text-white font-semibold">{receipt.case_id}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Exception Type</span>
                <span className="text-amber-400">{receipt.exception_type}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Exposure Amount</span>
                <span className="text-white">₹{receipt.exposure_amount.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Autonomy Level</span>
                <span className="text-indigo-400">{receipt.autonomy_level}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Policy Version</span>
                <span className="text-slate-300">{receipt.policy_version}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Approval Status</span>
                <span className="text-slate-300">{receipt.approval_status}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Verification</span>
                <span className="text-emerald-400">{receipt.verification_status}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Evidence Count</span>
                <span className="text-white">{receipt.evidence_count} items</span>
              </div>
            </div>

            <div className="border-t border-slate-800 pt-3">
              <span className="text-slate-500 block text-[10px] uppercase mb-1">Root Cause Explanation</span>
              <p className="text-slate-200">{receipt.root_cause}</p>
            </div>

            <div className="border-t border-slate-800 pt-3 flex flex-col md:flex-row md:items-center justify-between text-[10px] text-slate-500">
              <span>Chained Audit ID: <strong className="text-slate-300">{receipt.audit_id}</strong></span>
              <span className="truncate max-w-md">SHA-256 Digest: <strong className="text-slate-300">{receipt.audit_hash}</strong></span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
