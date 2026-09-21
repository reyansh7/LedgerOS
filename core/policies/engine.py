"""Deterministic Financial Policy Engine evaluating proposed agent actions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
import yaml

from core.config import settings


@dataclass
class PolicyEvaluationResult:
    verdict: str  # ALLOW, DENY, REQUIRE_APPROVAL
    policy_code: str
    reason: str
    amount_evaluated: Decimal
    action_type: str
    policy_version: str = "FIN-POL-v2.0"
    autonomy_level: str = "L4_AUTONOMOUS_EXECUTION"  # L0_DETECT, L1_INVESTIGATE, L2_RECOMMEND, L3_EXECUTE_WITH_APPROVAL, L4_AUTONOMOUS_EXECUTION


class FinancialPolicyEngine:
    """Evaluates proposed actions against deterministic financial rules, exposure boundaries, and autonomy levels."""

    def __init__(self, rules_file: Path | str | None = None):
        if rules_file is None:
            rules_file = Path(__file__).resolve().parent / "rules.yaml"
        self.rules_file = Path(rules_file)
        self.rules: dict[str, Any] = {}
        self.load_rules()

    def load_rules(self) -> None:
        if self.rules_file.exists():
            with self.rules_file.open("r", encoding="utf-8") as f:
                self.rules = yaml.safe_load(f) or {}

    @property
    def version(self) -> str:
        return f"FIN-POL-v{self.rules.get('version', '2.0')}"

    def evaluate(
        self,
        action_type: str,
        amount: Decimal | float | int,
        context: Optional[dict[str, Any]] = None,
    ) -> PolicyEvaluationResult:
        amt = Decimal(str(amount))
        ctx = context or {}
        action_upper = action_type.upper()
        pol_ver = self.version

        # 1. High Risk Actions check
        high_risk = self.rules.get("thresholds", {}).get("high_risk_actions", {})
        if action_upper in high_risk.get("actions", []):
            return PolicyEvaluationResult(
                verdict="REQUIRE_APPROVAL",
                policy_code="FIN-POL-RISK-01",
                reason=f"Action '{action_upper}' is classified as a high-risk operational action requiring human sign-off.",
                amount_evaluated=amt,
                action_type=action_upper,
                policy_version=pol_ver,
                autonomy_level="L3_EXECUTE_WITH_APPROVAL",
            )

        # 2. Refund / Recovery checks
        if "REFUND" in action_upper or "RECOVERY" in action_upper:
            ref_rules = self.rules.get("thresholds", {}).get("refund", {})
            max_auto = Decimal(str(ref_rules.get("max_auto_amount", 5000.0)))
            max_daily = Decimal(str(ref_rules.get("max_daily_exposure", 100000.0)))

            if amt > max_daily:
                return PolicyEvaluationResult(
                    verdict="DENY",
                    policy_code="FIN-POL-REF-03",
                    reason=f"Requested amount ({amt}) exceeds maximum allowable single exposure ({max_daily}). Action denied.",
                    amount_evaluated=amt,
                    action_type=action_upper,
                    policy_version=pol_ver,
                    autonomy_level="L2_RECOMMEND",
                )
            elif amt > max_auto:
                return PolicyEvaluationResult(
                    verdict="REQUIRE_APPROVAL",
                    policy_code="FIN-POL-REF-02",
                    reason=f"Amount ({amt}) exceeds auto-execution limit ({max_auto}). Requires human approval.",
                    amount_evaluated=amt,
                    action_type=action_upper,
                    policy_version=pol_ver,
                    autonomy_level="L3_EXECUTE_WITH_APPROVAL",
                )
            else:
                return PolicyEvaluationResult(
                    verdict="ALLOW",
                    policy_code="FIN-POL-REF-01",
                    reason=f"Amount ({amt}) is within bounded auto-execution limit ({max_auto}).",
                    amount_evaluated=amt,
                    action_type=action_upper,
                    policy_version=pol_ver,
                    autonomy_level="L4_AUTONOMOUS_EXECUTION",
                )

        # 3. Void Invoice checks
        if "VOID" in action_upper:
            void_rules = self.rules.get("thresholds", {}).get("void_invoice", {})
            max_auto = Decimal(str(void_rules.get("max_auto_amount", 25000.0)))
            if amt > max_auto:
                return PolicyEvaluationResult(
                    verdict="REQUIRE_APPROVAL",
                    policy_code="FIN-POL-VOID-02",
                    reason=f"Invoice void total ({amt}) exceeds auto-void limit ({max_auto}).",
                    amount_evaluated=amt,
                    action_type=action_upper,
                    policy_version=pol_ver,
                    autonomy_level="L3_EXECUTE_WITH_APPROVAL",
                )
            return PolicyEvaluationResult(
                verdict="ALLOW",
                policy_code="FIN-POL-VOID-01",
                reason=f"Void authorized for amount {amt} under policy limit {max_auto}.",
                amount_evaluated=amt,
                action_type=action_upper,
                policy_version=pol_ver,
                autonomy_level="L4_AUTONOMOUS_EXECUTION",
            )

        # Default fallback: safe bounded check
        if amt > Decimal("10000.0"):
            return PolicyEvaluationResult(
                verdict="REQUIRE_APPROVAL",
                policy_code="FIN-POL-GEN-02",
                reason=f"Transaction volume {amt} requires manual review by Finance Controller.",
                amount_evaluated=amt,
                action_type=action_upper,
                policy_version=pol_ver,
                autonomy_level="L3_EXECUTE_WITH_APPROVAL",
            )

        return PolicyEvaluationResult(
            verdict="ALLOW",
            policy_code="FIN-POL-GEN-01",
            reason="Action conforms to standard operational policy limits.",
            amount_evaluated=amt,
            action_type=action_upper,
            policy_version=pol_ver,
            autonomy_level="L4_AUTONOMOUS_EXECUTION",
        )


policy_engine = FinancialPolicyEngine()
