"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, Check, X, Clock, AlertTriangle, ShieldCheck } from "lucide-react";

interface ApprovalItem {
  approval_id: string;
  action_id: string;
  case_id: string;
  action_type: string;
  amount: number;
  currency: string;
  reason: string;
  policy_citation: string;
  status: string;
  created_at: string;
  reviewed_by: string | null;
  review_comment: string | null;
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState<string | null>(null);

  const fetchApprovals = () => {
    fetch("/api/approvals")
      .then((res) => res.json())
      .then((data) => setApprovals(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleAction = async (approvalId: string, verdict: "APPROVED" | "REJECTED") => {
    setActioningId(approvalId);
    try {
      await fetch(`/api/approvals/${approvalId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: json({ verdict, reviewer: "Finance Controller", comment: `Decision ${verdict} via LedgerOS Command Center` }),
      });
      fetchApprovals();
    } catch (e) {
      console.error(e);
    } finally {
      setActioningId(null);
    }
  };

  const json = (obj: any) => JSON.stringify(obj);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <ShieldAlert className="h-6 w-6 text-amber-400" />
          Human-in-the-Loop Governance &amp; Action Approvals
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Autonomous agents pause here at deterministic policy gates when financial actions exceed exposure limits.
        </p>
      </div>

      <div className="space-y-4">
        {approvals.length === 0 ? (
          <div className="p-12 rounded-xl bg-slate-900/40 border border-slate-800 text-center">
            <ShieldCheck className="h-10 w-10 text-emerald-400 mx-auto mb-3" />
            <div className="text-base font-semibold text-white">All Policy Gates Clear</div>
            <p className="text-xs text-slate-400 mt-1">
              No pending financial actions require manual sign-off at this time.
            </p>
          </div>
        ) : (
          approvals.map((app) => {
            const isPending = app.status === "PENDING";
            return (
              <div
                key={app.approval_id}
                className={`p-5 rounded-xl border transition ${
                  isPending
                    ? "bg-slate-900/80 border-amber-500/40 shadow-lg shadow-amber-500/5"
                    : "bg-slate-950/50 border-slate-800/80 opacity-75"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-amber-400">{app.approval_id}</span>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {app.policy_citation}
                      </span>
                      <span
                        className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-semibold ${
                          app.status === "APPROVED"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : app.status === "REJECTED"
                            ? "bg-rose-500/20 text-rose-400"
                            : "bg-amber-500/20 text-amber-300"
                        }`}
                      >
                        {app.status}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-white mt-1">
                      Proposed Action: <span className="text-blue-400">{app.action_type}</span> for Case{" "}
                      <span className="font-mono text-slate-300">{app.case_id}</span>
                    </h3>

                    <p className="text-xs text-slate-300 mt-1 max-w-2xl">{app.reason}</p>
                  </div>

                  <div className="flex flex-col sm:items-end gap-2 shrink-0">
                    <div className="text-sm font-mono font-bold text-white">
                      Exposure: <span className="text-rose-400">₹{app.amount.toLocaleString()}</span>
                    </div>

                    {isPending ? (
                      <div className="flex items-center gap-2 mt-1">
                        <button
                          onClick={() => handleAction(app.approval_id, "REJECTED")}
                          disabled={actioningId === app.approval_id}
                          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition flex items-center gap-1.5"
                        >
                          <X className="h-3.5 w-3.5 text-rose-400" /> Reject
                        </button>
                        <button
                          onClick={() => handleAction(app.approval_id, "APPROVED")}
                          disabled={actioningId === app.approval_id}
                          className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition flex items-center gap-1.5"
                        >
                          <Check className="h-3.5 w-3.5" /> Approve &amp; Execute
                        </button>
                      </div>
                    ) : (
                      <div className="text-[11px] font-mono text-slate-400">
                        Reviewed by {app.reviewed_by || "Manager"}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
