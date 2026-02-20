"""
Awareness Manifest - Tribal Principles Made Operational

Every Ganuda service must declare its tribal awareness through
a manifest that answers:
- WHO does this serve?
- AT WHOSE EXPENSE?
- Does it pass the SEVEN GENERATIONS test?
- What CONSENT is required?
- What COMMUNITY RETURN does it provide?

Based on: ULTRATHINK-TRIBAL-AWARENESS-INTEGRATION-JAN24-2026.md
Reference: DARRELLS_DEEP_QUESTION_TO_JRS.md (Oct 14,2025)
"""

import yaml
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class PotentialHarm:
    """A harm that this service might cause."""
    entity: str  # Who might be harmed
    description: str  # What the harm is
    mitigation: str  # How we prevent/reduce it
    residual_risk: str  # What risk remains after mitigation


@dataclass
class SevenGenerationsTest:
    """Assessment against 175-year impact."""
    question: str  # The specific question asked
    answer: str  # Our answer
    turtle_concern: str  # What Turtle specialist raised
    turtle_resolution: str  # How we addressed it


@dataclass
class ConsentRequirement:
    """Consent needed for this service."""
    data_type: str  # What data
    collection_consent: str  # How we get consent to collect
    retention_consent: str  # How we get consent to keep
    default_retention: str  # Default retention period
    withdrawal_process: str  # How user withdraws consent


@dataclass
class CommunityReturn:
    """What this service gives back."""
    artifact: str  # What we're sharing
    license: str  # Under what terms
    access: str  # How to access it
    benefit: str  # Who benefits and how


@dataclass
class AwarenessManifest:
    """
    Complete tribal awareness declaration for a service.

    Every service in Ganuda must have one of these.
    """
    service_name: str
    version: str
    last_updated: str

    # Triple Ethics Test (Darrell's Deep Question)
    primary_beneficiary: str
    secondary_beneficiaries: List[str]
    potential_harms: List[PotentialHarm]

    # Seven Generations
    seven_generations: SevenGenerationsTest

    # Consent Framework
    consent_requirements: List[ConsentRequirement]

    # Community Return
    community_returns: List[CommunityReturn]

    # Mitakuye Oyasin (All My Relations)
    relations_considered: List[str] = field(default_factory=list)

    @classmethod
    def load_from_yaml(cls, filepath: str) -> 'AwarenessManifest':
        """Load manifest from YAML file."""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        return cls(
            service_name=data['service_name'],
            version=data['version'],
            last_updated=data.get('last_updated', datetime.now().isoformat()),
            primary_beneficiary=data['tribal_awareness']['primary_beneficiary'],
            secondary_beneficiaries=data['tribal_awareness'].get('secondary_beneficiaries', []),
            potential_harms=[
                PotentialHarm(**h) for h in data['tribal_awareness'].get('potential_harms', [])
            ],
            seven_generations=SevenGenerationsTest(**data['tribal_awareness']['seven_generations']),
            consent_requirements=[
                ConsentRequirement(**c) for c in data['tribal_awareness'].get('consent_requirements', [])
            ],
            community_returns=[
                CommunityReturn(**r) for r in data['tribal_awareness'].get('community_returns', [])
            ],
            relations_considered=data['tribal_awareness'].get('relations_considered', [])
        )

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate manifest completeness.

        Returns (is_valid, list_of_issues)
        """
        issues = []

        # Must have primary beneficiary
        if not self.primary_beneficiary:
            issues.append("Missing primary_beneficiary - WHO does this serve?")

        # Must consider potential harms
        if not self.potential_harms:
            issues.append("Missing potential_harms - AT WHOSE EXPENSE?")

        # Each harm must have mitigation
        for harm in self.potential_harms:
            if not harm.mitigation:
                issues.append(f"Harm to '{harm.entity}' has no mitigation")

        # Must have Seven Generations test
        if not self.seven_generations.question:
            issues.append("Missing seven_generations question")
        if not self.seven_generations.turtle_concern:
            issues.append("Missing Turtle's concern (Seven Generations keeper)")

        # Must have at least one consent requirement if collecting data
        # (Services that don't collect data can skip this)

        # Must have at least one community return
        if not self.community_returns:
            issues.append("Missing community_returns - what does this give back?")

        return (len(issues) == 0, issues)

    def to_audit_record(self) -> dict:
        """Generate audit record for thermal memory."""
        return {
            "type": "awareness_manifest",
            "service": self.service_name,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "beneficiary": self.primary_beneficiary,
            "harms_count": len(self.potential_harms),
            "mitigations_complete": all(h.mitigation for h in self.potential_harms),
            "seven_gen_addressed": bool(self.seven_generations.turtle_resolution),
            "community_returns_count": len(self.community_returns),
            "valid": self.validate()[0]
        }

    def generate_report(self) -> str:
        """Generate human-readable report."""
        lines = [
            f"# Awareness Manifest: {self.service_name}",
            f"**Version:** {self.version}",
            f"**Last Updated:** {self.last_updated}",
            "",
            "## Triple Ethics Test",
            "",
            "### Benefit Who?",
            f"**Primary:** {self.primary_beneficiary}",
        ]

        if self.secondary_beneficiaries:
            lines.append("**Secondary:**")
            for b in self.secondary_beneficiaries:
                lines.append(f"- {b}")

        lines.extend([
            "",
            "### At Whose Expense?",
        ])

        for harm in self.potential_harms:
            lines.extend([
                f"**{harm.entity}:**",
                f"- Harm: {harm.description}",
                f"- Mitigation: {harm.mitigation}",
                f"- Residual Risk: {harm.residual_risk}",
                ""
            ])

        lines.extend([
            "## Seven Generations Test",
            f"**Question:** {self.seven_generations.question}",
            f"**Answer:** {self.seven_generations.answer}",
            f"**Turtle's Concern:** {self.seven_generations.turtle_concern}",
            f"**Resolution:** {self.seven_generations.turtle_resolution}",
            "",
            "## Community Return",
        ])

        for ret in self.community_returns:
            lines.extend([
                f"**{ret.artifact}:**",
                f"- License: {ret.license}",
                f"- Access: {ret.access}",
                f"- Benefit: {ret.benefit}",
                ""
            ])

        return "\n".join(lines)


def check_service_manifest(service_dir: str) -> tuple[bool, str]:
    """
    Check if a service has a valid awareness manifest.

    Returns (has_valid_manifest, message)
    """
    manifest_path = os.path.join(service_dir, "awareness_manifest.yaml")

    if not os.path.exists(manifest_path):
        return False, f"No awareness_manifest.yaml found in {service_dir}"

    try:
        manifest = AwarenessManifest.load_from_yaml(manifest_path)
        is_valid, issues = manifest.validate()

        if is_valid:
            return True, f"Valid manifest for {manifest.service_name}"
        else:
            return False, f"Invalid manifest: {'; '.join(issues)}"

    except Exception as e:
        return False, f"Error loading manifest: {e}"


def audit_all_services(ganuda_root: str = "/ganuda") -> dict:
    """
    Audit all services for awareness manifests.

    Returns summary of compliance.
    """
    service_dirs = [
        "vetassist",
        "sag",
        "jr_executor",
        "lib/consciousness_cascade",
        "services/vision",
        "telegram_bot",
    ]

    results = {}
    for service_dir in service_dirs:
        full_path = os.path.join(ganuda_root, service_dir)
        if os.path.isdir(full_path):
            has_manifest, message = check_service_manifest(full_path)
            results[service_dir] = {
                "has_manifest": has_manifest,
                "message": message
            }

    compliant = sum(1 for r in results.values() if r["has_manifest"])
    total = len(results)

    return {
        "services": results,
        "compliant": compliant,
        "total": total,
        "compliance_rate": f"{(compliant/total)*100:.1f}%" if total > 0 else "N/A"
    }


if __name__ == "__main__":
    # Run audit
    results = audit_all_services()
    print(f"Awareness Manifest Compliance: {results['compliance_rate']}")
    print(f"Compliant: {results['compliant']}/{results['total']}")

    for service, status in results["services"].items():
        icon = "✅" if status["has_manifest"] else "❌"
        print(f"  {icon} {service}: {status['message']}")
