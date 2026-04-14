# /ganuda/backend/chiral_validation/security_self_audit.py

import os
import logging
from typing import List, Dict
from ganuda.backend.chiral_validation.models import SecurityAudit, AuditResult
from ganuda.backend.chiral_validation.utils import get_node_info, run_security_check, cross_substrate_validate

logger = logging.getLogger(__name__)

class SecuritySelfAudit:
    def __init__(self, node_id: str, target_nodes: List[str]):
        """
        Initialize the SecuritySelfAudit class.

        :param node_id: The ID of the node running the audit.
        :param target_nodes: A list of node IDs to be audited.
        """
        self.node_id = node_id
        self.target_nodes = target_nodes
        self.audits: List[SecurityAudit] = []

    def perform_audit(self) -> None:
        """
        Perform security audits on the target nodes.
        """
        for target_node in self.target_nodes:
            if target_node == self.node_id:
                logger.warning(f"Skipping self-audit for node {self.node_id}")
                continue

            node_info = get_node_info(target_node)
            if not node_info:
                logger.error(f"Failed to get info for node {target_node}")
                continue

            audit = SecurityAudit(node_id=target_node, node_info=node_info)
            audit_results = run_security_check(node_info)
            audit.results = audit_results

            # Cross-substrate validation
            if not cross_substrate_validate(audit_results, self.node_id):
                logger.error(f"Cross-substrate validation failed for node {target_node}")
                audit.status = "FAILED"
            else:
                audit.status = "PASSED"

            self.audits.append(audit)

    def generate_report(self) -> Dict[str, str]:
        """
        Generate a report of the audit results.

        :return: A dictionary containing the audit results.
        """
        report = {}
        for audit in self.audits:
            report[audit.node_id] = audit.status
        return report

def main() -> None:
    """
    Main function to run the security self-audit.
    """
    node_id = os.getenv("NODE_ID")
    target_nodes = os.getenv("TARGET_NODES", "").split(",")
    if not node_id or not target_nodes:
        logger.error("NODE_ID and TARGET_NODES environment variables must be set.")
        return

    auditor = SecuritySelfAudit(node_id, target_nodes)
    auditor.perform_audit()
    report = auditor.generate_report()
    print(report)

if __name__ == "__main__":
    main()