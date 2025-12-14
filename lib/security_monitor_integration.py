#!/usr/bin/env python3
"""
Security Monitor Integration Library
Cherokee AI Federation - Tool Call Monitoring for Daemons

This library provides easy integration between Cherokee AI daemons
and Security Monitor Jr for GTG-1002 attack pattern detection.

Usage:
    from security_monitor_integration import SecurityMonitorIntegration

    monitor = SecurityMonitorIntegration(daemon_name='memory_jr')

    # Log database access
    monitor.log_database_access('thermal_memory_db', 'SELECT', success=True)

    # Log network operation
    monitor.log_network_operation('100.112.254.96', 'ssh', success=True)

    # Log tool execution
    monitor.log_tool_call('file_read', '/etc/passwd', success=True)
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add daemons directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'daemons'))

try:
    from security_monitor_jr import SecurityMonitorJr
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    print("⚠️  Security Monitor Jr not available - monitoring disabled")


class SecurityMonitorIntegration:
    """
    Easy-to-use wrapper for Cherokee AI daemons to log security events

    Categorizes operations into high-level types that match GTG-1002
    attack patterns: database access, network operations, credential
    access, code execution, file operations, etc.
    """

    def __init__(self, daemon_name: str, session_id: Optional[str] = None):
        """
        Initialize monitoring integration

        Args:
            daemon_name: Name of daemon (memory_jr, integration_jr, etc.)
            session_id: Optional session ID (auto-generated if not provided)
        """
        self.daemon_name = daemon_name
        self.session_id = session_id or f"{daemon_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.enabled = MONITORING_AVAILABLE

        if self.enabled:
            self.monitor = SecurityMonitorJr()
            print(f"🔒 Security monitoring enabled for {daemon_name} (session: {self.session_id})")
        else:
            self.monitor = None
            print(f"⚠️  Security monitoring disabled for {daemon_name}")

    def log_database_access(self, database_name: str, operation: str,
                           success: bool = True, metadata: Optional[Dict] = None):
        """
        Log database access operation

        Args:
            database_name: Name of database (thermal_memory, zammad_production, etc.)
            operation: SQL operation (SELECT, INSERT, UPDATE, DELETE)
            success: Whether operation succeeded
            metadata: Additional context (query, rows affected, etc.)
        """
        if not self.enabled:
            return

        start_time = time.time()
        tool_name = f"database_access"
        target = f"{database_name}:{operation}"

        self.monitor.log_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            target=target,
            success=success,
            duration_ms=int((time.time() - start_time) * 1000),
            metadata={
                'daemon': self.daemon_name,
                'database': database_name,
                'operation': operation,
                **(metadata or {})
            }
        )

    def log_network_operation(self, host: str, operation: str,
                             success: bool = True, metadata: Optional[Dict] = None):
        """
        Log network operation

        Args:
            host: Target host (IP or hostname)
            operation: Type of operation (ssh, http, api_call, etc.)
            success: Whether operation succeeded
            metadata: Additional context
        """
        if not self.enabled:
            return

        start_time = time.time()

        # Map to GTG-1002 attack patterns
        if 'scan' in operation.lower() or 'recon' in operation.lower():
            tool_name = "network_scan"
        elif 'ssh' in operation.lower() or 'remote' in operation.lower():
            tool_name = "lateral_movement"
        else:
            tool_name = "network_operation"

        self.monitor.log_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            target=host,
            success=success,
            duration_ms=int((time.time() - start_time) * 1000),
            metadata={
                'daemon': self.daemon_name,
                'operation': operation,
                **(metadata or {})
            }
        )

    def log_credential_access(self, credential_type: str, target: str,
                             success: bool = True, metadata: Optional[Dict] = None):
        """
        Log credential access (HIGH SENSITIVITY)

        Args:
            credential_type: Type of credential (password, api_key, token, ssh_key)
            target: What the credential is for
            success: Whether access succeeded
            metadata: Additional context (NEVER include actual credentials)
        """
        if not self.enabled:
            return

        start_time = time.time()
        tool_name = "credential_access"

        self.monitor.log_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            target=f"{credential_type}:{target}",
            success=success,
            duration_ms=int((time.time() - start_time) * 1000),
            metadata={
                'daemon': self.daemon_name,
                'credential_type': credential_type,
                'sensitivity': 'HIGH',
                **(metadata or {})
            }
        )

    def log_code_execution(self, code_type: str, target: Optional[str] = None,
                          success: bool = True, metadata: Optional[Dict] = None):
        """
        Log code execution

        Args:
            code_type: Type of code (python, bash, sql, etc.)
            target: What the code operated on
            success: Whether execution succeeded
            metadata: Additional context
        """
        if not self.enabled:
            return

        start_time = time.time()

        # Map to attack patterns
        if 'exploit' in str(metadata).lower():
            tool_name = "exploit_development"
        else:
            tool_name = "code_execution"

        self.monitor.log_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            target=target or code_type,
            success=success,
            duration_ms=int((time.time() - start_time) * 1000),
            metadata={
                'daemon': self.daemon_name,
                'code_type': code_type,
                **(metadata or {})
            }
        )

    def log_file_operation(self, operation: str, file_path: str,
                          success: bool = True, metadata: Optional[Dict] = None):
        """
        Log file system operation

        Args:
            operation: Type of operation (read, write, delete, modify)
            file_path: Path to file
            success: Whether operation succeeded
            metadata: Additional context
        """
        if not self.enabled:
            return

        start_time = time.time()

        # Flag sensitive paths
        sensitive_paths = ['/etc/passwd', '/etc/shadow', '/.ssh/', '/credentials', '/secrets']
        is_sensitive = any(sp in file_path for sp in sensitive_paths)

        tool_name = f"file_{operation}"

        self.monitor.log_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            target=file_path,
            success=success,
            duration_ms=int((time.time() - start_time) * 1000),
            metadata={
                'daemon': self.daemon_name,
                'operation': operation,
                'sensitive': is_sensitive,
                **(metadata or {})
            }
        )

    def log_data_transfer(self, source: str, destination: str, size_bytes: int,
                         success: bool = True, metadata: Optional[Dict] = None):
        """
        Log data transfer operation (CRITICAL FOR EXFILTRATION DETECTION)

        Args:
            source: Source of data
            destination: Destination of data
            size_bytes: Size of transfer
            success: Whether transfer succeeded
            metadata: Additional context
        """
        if not self.enabled:
            return

        start_time = time.time()

        # Flag external transfers
        is_external = not any(dest in destination for dest in
                             ['localhost', '127.0.0.1', '192.168.', '10.', '100.'])

        tool_name = "external_transfer" if is_external else "data_transfer"

        self.monitor.log_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            target=f"{source} → {destination}",
            success=success,
            duration_ms=int((time.time() - start_time) * 1000),
            metadata={
                'daemon': self.daemon_name,
                'source': source,
                'destination': destination,
                'size_bytes': size_bytes,
                'external': is_external,
                'sensitivity': 'CRITICAL' if is_external else 'MEDIUM',
                **(metadata or {})
            }
        )

    def log_thermal_memory_operation(self, operation: str, temperature: float,
                                     tags: list, success: bool = True,
                                     metadata: Optional[Dict] = None):
        """
        Log thermal memory operations (Cherokee-specific)

        Args:
            operation: Type of operation (store, recall, update)
            temperature: Temperature of memory
            tags: Memory tags
            success: Whether operation succeeded
            metadata: Additional context
        """
        if not self.enabled:
            return

        start_time = time.time()

        # Flag sacred/constitutional operations
        is_sacred = temperature >= 95.0
        tool_name = f"thermal_memory_{operation}"

        self.monitor.log_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            target=f"temp={temperature}°C",
            success=success,
            duration_ms=int((time.time() - start_time) * 1000),
            metadata={
                'daemon': self.daemon_name,
                'operation': operation,
                'temperature': temperature,
                'tags': tags,
                'sacred': is_sacred,
                'sensitivity': 'CONSTITUTIONAL' if is_sacred else 'HIGH',
                **(metadata or {})
            }
        )

    def log_tool_call(self, tool_name: str, target: Optional[str] = None,
                     success: bool = True, metadata: Optional[Dict] = None):
        """
        Generic tool call logging (use specific methods when possible)

        Args:
            tool_name: Name of tool
            target: Target of operation
            success: Whether operation succeeded
            metadata: Additional context
        """
        if not self.enabled:
            return

        start_time = time.time()

        self.monitor.log_tool_call(
            session_id=self.session_id,
            tool_name=tool_name,
            target=target,
            success=success,
            duration_ms=int((time.time() - start_time) * 1000),
            metadata={
                'daemon': self.daemon_name,
                **(metadata or {})
            }
        )


# Convenience function for daemons
def create_monitor(daemon_name: str, session_id: Optional[str] = None) -> SecurityMonitorIntegration:
    """
    Create security monitor integration for a daemon

    Usage:
        monitor = create_monitor('memory_jr')
        monitor.log_database_access('thermal_memory', 'SELECT')
    """
    return SecurityMonitorIntegration(daemon_name, session_id)


# Example integration for existing daemons
if __name__ == '__main__':
    print("🔒 Security Monitor Integration - Example Usage\n")

    # Simulate Memory Jr operations
    print("Example 1: Memory Jr accessing thermal memory")
    monitor = create_monitor('memory_jr')
    monitor.log_database_access('thermal_memory', 'SELECT', metadata={'query': 'sacred memories'})
    monitor.log_thermal_memory_operation('recall', temperature=95.0, tags=['constitutional', 'security'])

    print("\nExample 2: Integration Jr network operations")
    monitor2 = create_monitor('integration_jr')
    monitor2.log_network_operation('100.112.254.96', 'ssh', metadata={'purpose': 'federation sync'})
    monitor2.log_database_access('zammad_production', 'UPDATE')

    print("\nExample 3: Simulating GTG-1002-style attack")
    monitor3 = create_monitor('malicious_actor')
    monitor3.log_network_operation('192.168.1.1', 'network_scan')
    monitor3.log_tool_call('vulnerability_research', 'CVE-2024-1234')
    monitor3.log_code_execution('python', metadata={'exploit': True})
    monitor3.log_credential_access('ssh_key', 'production_server')
    monitor3.log_database_access('customer_db', 'SELECT')
    monitor3.log_data_transfer('customer_db', 'attacker.com', 1000000)

    print("\n✅ Integration examples complete. Check Security Monitor Jr for alerts:")
    print("    python3 /Users/Shared/ganuda/daemons/security_monitor_jr.py alerts")
