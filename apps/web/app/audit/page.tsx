"use client";

import { useEffect, useState } from "react";
import { History, ShieldCheck, Hash, Link2, RefreshCw, Lock, AlertTriangle, CheckCircle2 } from "lucide-react";

interface AuditEvent {
  audit_id: string;
  agent_name: string;
  action_type: string;
  case_id: string | null;
  decision: string;
  policy_code: string | null;
  confidence_score: number;
  human_approval: boolean;
  human_reviewer: string | null;
  execution_result: string;
  hash_digest: string;
  previous_hash: string;
  timestamp: string;
}

interface VerificationResult {
  valid: boolean;
  total_events: number;
  verified_blocks: number;
  genesis_hash?: string;
  head_hash?: string;
  failed_at_audit_id?: string;
  reason?: string;
}

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [verification, setVerification] = useState<VerificationResult | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAudit = () => {
    fetch("/api/audit?limit=100")
      .then((res) => res.json())
      .then((data) => setEvents(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const runVerification = async () => {
    setVerifying(true);
    try {
      const res = await fetch("/api/audit/verify");
      if (res.ok) {
        const data = await res.json();
        setVerification(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    fetchAudit();
    runVerification();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <History className="h-6 w-6 text-emerald-400" />
            Immutable Audit Trail &amp; Provenance Ledger
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Cryptographically chained (SHA-256) audit trail recording every agent decision, policy check, human approval, and recovery execution.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start">
          <button
            onClick={runVerification}
            disabled={verifying}
            className="px-3 py-1.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30 text-xs font-medium text-emerald-400 hover:bg-emerald-900/40 transition flex items-center gap-1.5 disabled:opacity-50"
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            {verifying ? "Verifying SHA-256..." : "Verify Hash Integrity"}
          </button>

          <button
            onClick={() => {
              fetchAudit();
              runVerification();
            }}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:bg-slate-800 transition flex items-center gap-1.5"
          >
            <RefreshCw className="h-3 w-3" /> Refresh Ledger
          </button>
        </div>
      </div>

      <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between font-mono text-xs text-slate-400">
          <span>CHAINED AUDIT EVENTS ({events.length})</span>
          {verification?.valid ? (
            <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
              <Lock className="h-3.5 w-3.5" /> SHA-256 HASH CHAIN VERIFIED ({verification.verified_blocks} BLOCKS)
            </span>
          ) : verification && !verification.valid ? (
            <span className="flex items-center gap-1.5 text-rose-400 font-bold bg-rose-950/40 px-2 py-0.5 rounded border border-rose-500/40">
              <AlertTriangle className="h-3.5 w-3.5" /> CHAIN INTEGRITY FAILURE ({verification.failed_at_audit_id})
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-slate-400">
              <Lock className="h-3 w-3" /> Verifying chain...
            </span>
          )}
        </div>

        <div className="divide-y divide-slate-800/60 font-mono text-xs">
          {events.map((e, idx) => (
            <div key={e.audit_id} className="p-4 hover:bg-slate-800/20 transition space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className="font-bold text-blue-400">{e.audit_id}</span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                    {e.agent_name}
                  </span>
                  <span className="text-slate-200 font-semibold">{e.action_type}</span>
                  {e.case_id && (
                    <span className="text-slate-400 text-[11px]">Case: {e.case_id}</span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-[11px] text-slate-400">
                  <span>{e.timestamp}</span>
                  <span
                    className={`px-2 py-0.5 rounded uppercase font-semibold text-[10px] ${
                      e.decision === "APPROVED" || e.decision === "ALLOW"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-amber-500/20 text-amber-300"
                    }`}
                  >
                    {e.decision}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-500 pt-1">
                <div className="truncate flex items-center gap-1.5">
                  <Hash className="h-3 w-3 text-slate-400 shrink-0" />
                  <span>Hash Digest:</span>
                  <span className="text-slate-300">{e.hash_digest}</span>
                </div>
                <div className="truncate flex items-center gap-1.5">
                  <Link2 className="h-3 w-3 text-slate-400 shrink-0" />
                  <span>Chained From:</span>
                  <span className="text-slate-400">{e.previous_hash.slice(0, 24)}...</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
