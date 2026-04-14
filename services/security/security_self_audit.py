# /ganuda/services/security/security_self_audit.py

import os
import logging
from typing import List, Dict
from ganuda.services.core.node import Node
from ganuda.services.core.cluster import Cluster
from ganuda.services.security.fire_guard import FireGuard
from ganuda.services.security.safety_canary import SafetyCanary
from ganuda.services.security.credential_scanner import CredentialScanner

logger = logging.getLogger(__name__)

class SecuritySelfAudit:
    def __init__(self, cluster: Cluster):
        self.cluster = cluster
        self.nodes = cluster.get_nodes()
        self.audit_results: Dict[str, Dict] = {}

    def run_audit(self) -> None:
        """
        Runs a comprehensive security self-audit on the cluster.
        """
        logger.info("Starting security self-audit...")
        self.audit_fire_guard()
        self.audit_safety_canary()
        self.audit_credential_scanner()
        logger.info("Security self-audit completed.")

    def audit_fire_guard(self) -> None:
        """
        Audits the Fire Guard service on each node.
        """
        fire_guard = FireGuard()
        for node in self.nodes:
            result = fire_guard.run_scan(node)
            self.audit_results[node.name] = result
            logger.info(f"Fire Guard audit for {node.name}: {result}")

    def audit_safety_canary(self) -> None:
        """
        Audits the Safety Canary service on each node.
        """
        safety_canary = SafetyCanary()
        for node in self.nodes:
            result = safety_canary.run_check(node)
            self.audit_results[node.name].update(result)
            logger.info(f"Safety Canary audit for {node.name}: {result}")

    def audit_credential_scanner(self) -> None:
        """
        Audits the Credential Scanner service on each node.
        """
        credential_scanner = CredentialScanner()
        for node in self.nodes:
            result = credential_scanner.run_scan(node)
            self.audit_results[node.name].update(result)
            logger.info(f"Credential Scanner audit for {node.name}: {result}")

    def get_audit_results(self) -> Dict[str, Dict]:
        """
        Returns the results of the security self-audit.
        """
        return self.audit_results

if __name__ == "__main__":
    cluster = Cluster()
    audit = SecuritySelfAudit(cluster)
    audit.run_audit()
    results = audit.get_audit_results()
    print(results)