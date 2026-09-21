"""Typed Provenance Graph Retrieval for financial records.

Implements explicit schema-directed graph traversal over financial entities:
Vendor <-> PO <-> Invoice <-> Approval <-> Payment <-> Bank <-> GL
without relying on unstructured embeddings.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models.operational import (
    Vendor,
    VendorChangeLog,
    PurchaseOrder,
    POLine,
    Invoice,
    InvoiceLine,
    ApprovalEvent,
    Payment,
    PaymentAllocation,
    GLEntry,
    BankTransaction,
    BankStatement,
    Employee,
)


class ProvenanceGraphRetriever:
    """Traverses relational accounting links to gather complete causal evidence for a case."""

    def __init__(self, session: Session):
        self.session = session

    def get_provenance_subgraph(
        self,
        primary_entity_type: str,
        primary_entity_id: str,
        max_hops: int = 3,
    ) -> dict[str, Any]:
        """Traverse foreign keys and reference links starting from primary entity."""
        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, str]] = []
        visited: set[tuple[str, str]] = set()

        def add_node(entity_type: str, entity_id: str, data: dict[str, Any]):
            key = f"{entity_type}:{entity_id}"
            if key not in nodes:
                nodes[key] = {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "data": data,
                }

        def add_edge(src_type: str, src_id: str, dst_type: str, dst_id: str, rel: str):
            edges.append({
                "source": f"{src_type}:{src_id}",
                "target": f"{dst_type}:{dst_id}",
                "relation": rel,
            })

        # BFS queue: (entity_type, entity_id, current_hop)
        queue = [(primary_entity_type.lower(), primary_entity_id, 0)]
        visited.add((primary_entity_type.lower(), primary_entity_id))

        while queue:
            curr_type, curr_id, hop = queue.pop(0)

            if curr_type == "invoice":
                inv = self.session.execute(
                    select(Invoice).where(Invoice.invoice_id == curr_id)
                ).scalar_one_or_none()
                if inv:
                    add_node("invoice", inv.invoice_id, {
                        "invoice_id": inv.invoice_id,
                        "invoice_number": inv.invoice_number,
                        "vendor_id": inv.vendor_id,
                        "po_id": inv.po_id,
                        "invoice_total": float(inv.invoice_total),
                        "status": inv.status,
                        "duplicate_reference": inv.duplicate_reference,
                        "invoice_date": inv.invoice_date,
                    })

                    # Vendor link
                    if inv.vendor_id and ("vendor", inv.vendor_id) not in visited and hop < max_hops:
                        visited.add(("vendor", inv.vendor_id))
                        queue.append(("vendor", inv.vendor_id, hop + 1))
                        add_edge("invoice", inv.invoice_id, "vendor", inv.vendor_id, "ISSUED_BY")

                    # PO link
                    if inv.po_id and ("purchase_order", inv.po_id) not in visited and hop < max_hops:
                        visited.add(("purchase_order", inv.po_id))
                        queue.append(("purchase_order", inv.po_id, hop + 1))
                        add_edge("invoice", inv.invoice_id, "purchase_order", inv.po_id, "BASED_ON_PO")

                    # Invoice lines
                    lines = self.session.execute(
                        select(InvoiceLine).where(InvoiceLine.invoice_id == inv.invoice_id)
                    ).scalars().all()
                    for line in lines:
                        add_node("invoice_line", line.invoice_line_id, {
                            "invoice_line_id": line.invoice_line_id,
                            "po_line_id": line.po_line_id,
                            "item_id": line.item_id,
                            "quantity": float(line.quantity),
                            "unit_price": float(line.unit_price),
                            "line_amount": float(line.line_amount),
                        })
                        add_edge("invoice", inv.invoice_id, "invoice_line", line.invoice_line_id, "HAS_LINE")

                    # Approval events
                    approvals = self.session.execute(
                        select(ApprovalEvent).where(ApprovalEvent.invoice_id == inv.invoice_id)
                    ).scalars().all()
                    for app in approvals:
                        add_node("approval_event", app.approval_event_id, {
                            "approval_event_id": app.approval_event_id,
                            "approver_id": app.approver_id,
                            "action": app.action,
                            "new_status": app.new_status,
                            "comments": app.comments,
                        })
                        add_edge("invoice", inv.invoice_id, "approval_event", app.approval_event_id, "APPROVAL_LOG")

                    # Payment allocations -> Payments
                    allocs = self.session.execute(
                        select(PaymentAllocation).where(PaymentAllocation.invoice_id == inv.invoice_id)
                    ).scalars().all()
                    for alloc in allocs:
                        if ("payment", alloc.payment_id) not in visited and hop < max_hops:
                            visited.add(("payment", alloc.payment_id))
                            queue.append(("payment", alloc.payment_id, hop + 1))
                            add_edge("invoice", inv.invoice_id, "payment", alloc.payment_id, "PAID_BY")

                    # GL entries
                    gls = self.session.execute(
                        select(GLEntry).where(GLEntry.source_transaction_id == inv.invoice_id)
                    ).scalars().all()
                    for gl in gls:
                        add_node("gl_entry", gl.journal_line_id, {
                            "journal_line_id": gl.journal_line_id,
                            "gl_account": gl.gl_account,
                            "debit": float(gl.debit),
                            "credit": float(gl.credit),
                            "accounting_period": gl.accounting_period,
                        })
                        add_edge("invoice", inv.invoice_id, "gl_entry", gl.journal_line_id, "POSTED_TO_GL")

            elif curr_type == "purchase_order":
                po = self.session.execute(
                    select(PurchaseOrder).where(PurchaseOrder.po_id == curr_id)
                ).scalar_one_or_none()
                if po:
                    add_node("purchase_order", po.po_id, {
                        "po_id": po.po_id,
                        "vendor_id": po.vendor_id,
                        "po_total": float(po.po_total),
                        "status": po.status,
                        "po_date": po.po_date,
                    })
                    if po.vendor_id and ("vendor", po.vendor_id) not in visited and hop < max_hops:
                        visited.add(("vendor", po.vendor_id))
                        queue.append(("vendor", po.vendor_id, hop + 1))
                        add_edge("purchase_order", po.po_id, "vendor", po.vendor_id, "ORDERED_FROM")

                    # PO lines
                    polines = self.session.execute(
                        select(POLine).where(POLine.po_id == po.po_id)
                    ).scalars().all()
                    for pl in polines:
                        add_node("po_line", pl.po_line_id, {
                            "po_line_id": pl.po_line_id,
                            "item_id": pl.item_id,
                            "quantity": float(pl.quantity),
                            "unit_price": float(pl.unit_price),
                            "line_amount": float(pl.line_amount),
                        })
                        add_edge("purchase_order", po.po_id, "po_line", pl.po_line_id, "HAS_LINE")

            elif curr_type == "payment":
                pay = self.session.execute(
                    select(Payment).where(Payment.payment_id == curr_id)
                ).scalar_one_or_none()
                if pay:
                    add_node("payment", pay.payment_id, {
                        "payment_id": pay.payment_id,
                        "vendor_id": pay.vendor_id,
                        "payment_amount": float(pay.payment_amount),
                        "payment_status": pay.payment_status,
                        "reference_number": pay.reference_number,
                        "payment_date": pay.payment_date,
                    })

                    # Bank transaction link (via payment_reference or reference_number)
                    bt = None
                    if pay.reference_number:
                        bt = self.session.execute(
                            select(BankTransaction).where(
                                (BankTransaction.payment_reference == pay.reference_number) |
                                (BankTransaction.bank_reference == pay.reference_number)
                            )
                        ).scalar_one_or_none()
                    if bt:
                        add_node("bank_transaction", bt.bank_transaction_id, {
                            "bank_transaction_id": bt.bank_transaction_id,
                            "amount": float(bt.amount),
                            "direction": bt.direction,
                            "status": bt.status,
                            "bank_reference": bt.bank_reference,
                            "transaction_date": bt.transaction_date,
                        })
                        add_edge("payment", pay.payment_id, "bank_transaction", bt.bank_transaction_id, "CLEARED_IN_BANK")

                    # GL entries for payment
                    gls = self.session.execute(
                        select(GLEntry).where(GLEntry.source_transaction_id == pay.payment_id)
                    ).scalars().all()
                    for gl in gls:
                        add_node("gl_entry", gl.journal_line_id, {
                            "journal_line_id": gl.journal_line_id,
                            "gl_account": gl.gl_account,
                            "debit": float(gl.debit),
                            "credit": float(gl.credit),
                            "accounting_period": gl.accounting_period,
                        })
                        add_edge("payment", pay.payment_id, "gl_entry", gl.journal_line_id, "POSTED_TO_GL")

            elif curr_type == "bank_transaction":
                bt = self.session.execute(
                    select(BankTransaction).where(BankTransaction.bank_transaction_id == curr_id)
                ).scalar_one_or_none()
                if bt:
                    add_node("bank_transaction", bt.bank_transaction_id, {
                        "bank_transaction_id": bt.bank_transaction_id,
                        "amount": float(bt.amount),
                        "bank_reference": bt.bank_reference,
                        "payment_reference": bt.payment_reference,
                        "direction": bt.direction,
                        "transaction_date": bt.transaction_date,
                    })
                    # Try to link to payment
                    if bt.payment_reference:
                        pay = self.session.execute(
                            select(Payment).where(
                                (Payment.reference_number == bt.payment_reference) |
                                (Payment.payment_id == bt.payment_reference)
                            )
                        ).scalar_one_or_none()
                        if pay and ("payment", pay.payment_id) not in visited and hop < max_hops:
                            visited.add(("payment", pay.payment_id))
                            queue.append(("payment", pay.payment_id, hop + 1))
                            add_edge("bank_transaction", bt.bank_transaction_id, "payment", pay.payment_id, "MATCHES_PAYMENT")

            elif curr_type == "vendor":
                vnd = self.session.execute(
                    select(Vendor).where(Vendor.vendor_id == curr_id)
                ).scalar_one_or_none()
                if vnd:
                    add_node("vendor", vnd.vendor_id, {
                        "vendor_id": vnd.vendor_id,
                        "vendor_name": vnd.vendor_name,
                        "vendor_status": vnd.vendor_status,
                        "payment_terms": vnd.payment_terms,
                    })
                    # Vendor changes
                    changes = self.session.execute(
                        select(VendorChangeLog).where(VendorChangeLog.vendor_id == vnd.vendor_id)
                    ).scalars().all()
                    for chg in changes:
                        add_node("vendor_change", chg.change_id, {
                            "change_id": chg.change_id,
                            "field_changed": chg.field_changed,
                            "old_value": chg.old_value,
                            "new_value": chg.new_value,
                            "changed_at": chg.changed_at,
                        })
                        add_edge("vendor", vnd.vendor_id, "vendor_change", chg.change_id, "MODIFIED_BY")

        evidence_ids = [n["entity_id"] for n in nodes.values()]
        return {
            "root_entity": f"{primary_entity_type}:{primary_entity_id}",
            "evidence_count": len(nodes),
            "evidence_ids": evidence_ids,
            "nodes": list(nodes.values()),
            "edges": edges,
        }
