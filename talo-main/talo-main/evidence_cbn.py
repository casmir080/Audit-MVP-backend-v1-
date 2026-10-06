"""
CBN Payment Data Localisation -- Evidence Schema (v1)

Grounded in CBN Circular PSS/DIR/PUB/CIR/001/004 (15 June 2026) and the
standard preparation steps Nigerian compliance-advisory firms are
recommending in response to it. Full compliance is required from
1 January 2027.

Scope: Deposit Money Banks, Microfinance Banks, Mobile Money Operators,
switching/processing companies, Payment Terminal/Solution Service
Providers, Super Agents, and other licensed payment participants.

This is a v1 starting point, not a verified legal checklist -- validate
against the primary circular text and legal counsel before using it to
make representations to a regulator or a client.

Designed to be dropped alongside your existing evidence-sufficiency
engine: swap the scoring/storage logic below for your real pipeline.
No external dependencies -- adapt to pydantic/Django/whatever your
stack uses.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EvidenceCategory(str, Enum):
    DATA_INVENTORY = "data_system_inventory"
    INFRA_HOSTING = "infrastructure_hosting_assessment"
    VENDOR_CONTRACTS = "vendor_contract_review"
    BACKUP_DR = "backup_dr_key_management"
    GOVERNANCE = "governance_oversight"
    UBO = "ubo_disclosure"  # bundled in the same circular, separate workstream


class Criticality(str, Enum):
    BLOCKING = "blocking"  # no credible compliance story without this
    HIGH = "high"
    MEDIUM = "medium"


@dataclass
class EvidenceItem:
    id: str
    category: EvidenceCategory
    description: str
    required_doc_types: list
    criticality: Criticality
    notes: Optional[str] = None


# --- v1 checklist, informed by public advisory guidance on the circular ---
CBN_LOCALISATION_EVIDENCE = [
    EvidenceItem(
        id="DI-1",
        category=EvidenceCategory.DATA_INVENTORY,
        description="Full inventory of systems that store, process, or transmit "
                    "Nigeria-generated payment transaction data",
        required_doc_types=["system inventory doc", "data flow diagram"],
        criticality=Criticality.BLOCKING,
    ),
    EvidenceItem(
        id="DI-2",
        category=EvidenceCategory.DATA_INVENTORY,
        description="Data-mapping exercise showing where each data element is "
                    "generated, stored, processed and transmitted",
        required_doc_types=["data mapping report"],
        criticality=Criticality.BLOCKING,
    ),
    EvidenceItem(
        id="IH-1",
        category=EvidenceCategory.INFRA_HOSTING,
        description="Hosting location confirmed for the primary transaction database(s)",
        required_doc_types=["infrastructure diagram", "cloud provider region confirmation"],
        criticality=Criticality.BLOCKING,
        notes="CBN hasn't clarified whether a foreign hyperscaler's local availability "
              "zone counts as compliant -- track as an open item, don't assume.",
    ),
    EvidenceItem(
        id="IH-2",
        category=EvidenceCategory.INFRA_HOSTING,
        description="Hosting location confirmed for logs, backups and disaster-recovery "
                    "copies, not just the primary database",
        required_doc_types=["backup/DR infrastructure diagram"],
        criticality=Criticality.HIGH,
    ),
    EvidenceItem(
        id="VC-1",
        category=EvidenceCategory.VENDOR_CONTRACTS,
        description="Third-party/offshore vendor contracts reviewed for data-residency "
                    "clauses that conflict with the directive",
        required_doc_types=["contract review log"],
        criticality=Criticality.HIGH,
    ),
    EvidenceItem(
        id="VC-2",
        category=EvidenceCategory.VENDOR_CONTRACTS,
        description="Remediation plan for contracts requiring renegotiation or "
                    "termination before the deadline",
        required_doc_types=["remediation plan"],
        criticality=Criticality.MEDIUM,
    ),
    EvidenceItem(
        id="BD-1",
        category=EvidenceCategory.BACKUP_DR,
        description="Encryption-key management confirmed consistent with in-country "
                    "storage requirements",
        required_doc_types=["key management policy"],
        criticality=Criticality.HIGH,
    ),
    EvidenceItem(
        id="GO-1",
        category=EvidenceCategory.GOVERNANCE,
        description="Board or management sign-off establishing oversight of the "
                    "localisation implementation programme",
        required_doc_types=["board minutes", "programme charter"],
        criticality=Criticality.HIGH,
    ),
    EvidenceItem(
        id="GO-2",
        category=EvidenceCategory.GOVERNANCE,
        description="Documented implementation roadmap tracked against the "
                    "1 January 2027 deadline",
        required_doc_types=["implementation roadmap"],
        criticality=Criticality.BLOCKING,
    ),
    EvidenceItem(
        id="UBO-1",
        category=EvidenceCategory.UBO,
        description="Up-to-date Ultimate Beneficial Owner register for significant shareholders",
        required_doc_types=["UBO register"],
        criticality=Criticality.MEDIUM,
        notes="Bundled into the same circular as a separate workstream -- build as its "
              "own module once the localisation module has pilot traction.",
    ),
]


def score_readiness(provided_evidence_ids: set) -> dict:
    """
    Minimal completeness scorer -- same shape you'd plug into your existing
    evidence-sufficiency engine. Replace with your real scoring logic.
    """
    missing_blocking = [
        item.id for item in CBN_LOCALISATION_EVIDENCE
        if item.criticality == Criticality.BLOCKING and item.id not in provided_evidence_ids
    ]
    total = len(CBN_LOCALISATION_EVIDENCE)
    provided = sum(1 for i in CBN_LOCALISATION_EVIDENCE if i.id in provided_evidence_ids)

    return {
        "completeness_pct": round(100 * provided / total, 1),
        "blocking_gaps": missing_blocking,
        "ready_for_pilot_report": len(missing_blocking) == 0,
    }


if __name__ == "__main__":
    # Example: a pilot customer has supplied evidence for 3 of the 10 items
    demo_provided = {"DI-1", "IH-1", "GO-1"}
    print(score_readiness(demo_provided))
