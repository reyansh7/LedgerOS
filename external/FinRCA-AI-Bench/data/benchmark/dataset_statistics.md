# FinRCA-Bench Dataset Statistics

Dataset hash: `8fe3e45510d0f410ce98620412d7cfde00403a434346335ee7684e8fb5b677fd`

Quality gate: **PASS**

## Case composition

- Total cases: 50
- Failure cases: 30
- Legitimate/no-failure cases: 20
- Difficulty: easy=17, hard=12, medium=21

## Table row counts

| Table | Rows |
|---|---:|
| vendors | 40 |
| vendor_change_log | 6 |
| purchase_orders | 160 |
| po_lines | 353 |
| invoices | 243 |
| invoice_lines | 539 |
| approval_events | 513 |
| payments | 184 |
| payment_allocations | 214 |
| gl_entries | 1394 |
| bank_transactions | 184 |
| bank_statements | 54 |
| employees | 24 |
| audit_log | 843 |

## Failure categories

| Category | Cases |
|---|---:|
| F01_DUPLICATE_INVOICE | 2 |
| F02_PO_INVOICE_AMOUNT_MISMATCH | 2 |
| F03_QUANTITY_MISMATCH | 2 |
| F04_INCORRECT_VENDOR_ASSOCIATION | 2 |
| F05_PAYMENT_WITHOUT_VALID_INVOICE | 2 |
| F06_INVOICE_PAID_TWICE | 2 |
| F07_PARTIAL_PAYMENT_RESIDUAL_BALANCE | 2 |
| F08_APPROVAL_WORKFLOW_FAILURE | 2 |
| F09_GL_POSTING_MISMATCH | 2 |
| F10_WRONG_ACCOUNTING_PERIOD | 2 |
| F11_VENDOR_MASTER_CHANGE_CONFLICT | 2 |
| F12_ERP_PAYMENT_MISSING_FROM_BANK | 2 |
| F13_BANK_TRANSACTION_MISSING_FROM_ERP | 2 |
| F14_BANK_ERP_AMOUNT_MISMATCH | 2 |
| F15_INCORRECT_PAYMENT_BANK_MATCH | 2 |

## Financial profile

Top-ten vendor spend share: 0.566420

Payment methods: {'ACH': 152, 'check': 16, 'wire': 16}

All records are synthetic and identifiers are tokenized. Post-injection reconciliation findings are intentional; the quality gate separately requires the clean baseline, double-entry journals, bank statements, evidence links, and split leakage checks to pass.
