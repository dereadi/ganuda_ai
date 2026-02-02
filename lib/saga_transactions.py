"""
SagaLLM Transaction Manager for Tsalagi Yohvwi Council

Implements distributed transaction guarantees from:
"SagaLLM: Context Management, Validation, and Transaction Guarantees
for Multi-Agent LLM Planning" (arXiv:2503.11951, VLDB 2025)

Key features:
- Three-state model: Application (S_A), Operation (S_O), Dependency (S_D)
- Compensating transactions for rollback
- GlobalValidationAgent for independent verification
- Checkpoint/recovery without full replan

For Seven Generations - ᏣᎳᎩ ᏲᏫᎢᎶᏗ
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import requests


class TransactionStatus(Enum):
    """Transaction lifecycle states."""
    PENDING = 'pending'
    EXECUTING = 'executing'
    VALIDATING = 'validating'
    COMMITTED = 'committed'
    COMPENSATING = 'compensating'
    ROLLED_BACK = 'rolled_back'
    FAILED = 'failed'


class ValidationType(Enum):
    """Types of validation performed by GlobalValidationAgent."""
    INTRA_AGENT = 'intra_agent'      # Single specialist response quality
    INTER_AGENT = 'inter_agent'      # Cross-specialist consistency
    CONSTRAINT = 'constraint'         # Domain constraint satisfaction
    SEMANTIC = 'semantic'             # Meaning and coherence
    TEMPORAL = 'temporal'             # Ordering and timing


@dataclass
class ApplicationState:
    """
    S_A: Application/Domain State
    Contains domain-specific entities and their current values.
    """
    query: str = ""
    query_id: str = ""
    domain: str = "general"
    entities: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'query': self.query,
            'query_id': self.query_id,
            'domain': self.domain,
            'entities': self.entities,
            'constraints': self.constraints
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ApplicationState':
        return cls(**data) if data else cls()


@dataclass
class OperationLog:
    """
    S_O: Operation State
    Contains transaction logs, decision chains, and compensation metadata.
    """
    operations: List[Dict] = field(default_factory=list)
    reasoning_chains: List[str] = field(default_factory=list)
    decisions: List[Dict] = field(default_factory=list)

    def append_operation(self, op_type: str, specialist: str, data: dict):
        self.operations.append({
            'type': op_type,
            'specialist': specialist,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })

    def append_reasoning(self, reasoning: str):
        self.reasoning_chains.append(reasoning)

    def append_decision(self, decision: dict):
        self.decisions.append({
            **decision,
            'timestamp': datetime.now().isoformat()
        })

    def to_dict(self) -> dict:
        return {
            'operations': self.operations,
            'reasoning_chains': self.reasoning_chains,
            'decisions': self.decisions
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'OperationLog':
        if not data:
            return cls()
        instance = cls()
        instance.operations = data.get('operations', [])
        instance.reasoning_chains = data.get('reasoning_chains', [])
        instance.decisions = data.get('decisions', [])
        return instance


@dataclass
class DependencyGraph:
    """
    S_D: Dependency State
    Contains graph-structured constraints and satisfaction criteria.
    """
    nodes: Dict[str, Dict] = field(default_factory=dict)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)  # (from, to, type)
    satisfied: Dict[str, bool] = field(default_factory=dict)

    def add_dependency(self, from_node: str, to_node: str, dep_type: str = 'requires'):
        if from_node not in self.nodes:
            self.nodes[from_node] = {'status': 'pending'}
        if to_node not in self.nodes:
            self.nodes[to_node] = {'status': 'pending'}
        self.edges.append((from_node, to_node, dep_type))

    def mark_satisfied(self, node: str, satisfied: bool = True):
        self.satisfied[node] = satisfied
        if node in self.nodes:
            self.nodes[node]['status'] = 'satisfied' if satisfied else 'failed'

    def all_dependencies_satisfied(self, node: str) -> bool:
        """Check if all dependencies of a node are satisfied."""
        for from_node, to_node, _ in self.edges:
            if to_node == node and not self.satisfied.get(from_node, False):
                return False
        return True

    def to_dict(self) -> dict:
        return {
            'nodes': self.nodes,
            'edges': self.edges,
            'satisfied': self.satisfied
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DependencyGraph':
        if not data:
            return cls()
        instance = cls()
        instance.nodes = data.get('nodes', {})
        instance.edges = [tuple(e) for e in data.get('edges', [])]
        instance.satisfied = data.get('satisfied', {})
        return instance


@dataclass
class CompensatingAction:
    """Defines how to undo an operation."""
    operation_type: str
    specialist: str
    compensation_fn: str  # Name of compensation function
    compensation_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'operation_type': self.operation_type,
            'specialist': self.specialist,
            'compensation_fn': self.compensation_fn,
            'compensation_data': self.compensation_data
        }


@dataclass
class ValidationIssue:
    """A single validation issue found."""
    issue_type: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    description: str
    specialist: Optional[str] = None
    remediation: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'type': self.issue_type,
            'severity': self.severity,
            'description': self.description,
            'specialist': self.specialist,
            'remediation': self.remediation
        }


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    validation_type: ValidationType
    issues: List[ValidationIssue] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            'is_valid': self.is_valid,
            'validation_type': self.validation_type.value,
            'issues': [i.to_dict() for i in self.issues],
            'confidence': self.confidence
        }


@dataclass
class Transaction:
    """
    Complete transaction state following SagaLLM three-state model.
    """
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_id: str = ""
    audit_hash: str = ""
    status: TransactionStatus = TransactionStatus.PENDING

    # Three-state model
    s_a: ApplicationState = field(default_factory=ApplicationState)
    s_o: OperationLog = field(default_factory=OperationLog)
    s_d: DependencyGraph = field(default_factory=DependencyGraph)

    # Metadata
    initiator: str = "council"
    priority: str = "normal"
    max_retries: int = 2
    current_retry: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    checkpoint_at: datetime = field(default_factory=datetime.now)
    committed_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None

    # Error tracking
    last_error: Optional[str] = None
    error_count: int = 0


class GlobalValidationAgent:
    """
    Independent validation agent - NOT self-assessment.

    Validates specialist responses from an external perspective,
    checking for issues the specialists themselves might miss.
    """

    def __init__(self, llm_endpoint: str = "http://100.116.27.89:8080/v1/chat/completions",
                 model: str = "/ganuda/models/qwen2.5-coder-32b-awq"):
        self.llm_endpoint = llm_endpoint
        self.model = model

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call LLM for validation."""
        try:
            response = requests.post(
                self.llm_endpoint,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3  # Low temperature for consistent validation
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return json.dumps({"valid": False, "error": str(e)})

    def validate_intra_agent(self, specialist: str, response: str,
                             context: str = "") -> ValidationResult:
        """
        Validate a single specialist's response.
        Checks: factual accuracy, logical consistency, constraint adherence.
        """
        system_prompt = f"""You are a validation agent, completely independent from {specialist}.
Your job is to critically evaluate their response for issues.

Check for:
1. FACTUAL: Claims that may be incorrect or unverifiable
2. LOGICAL: Reasoning that doesn't follow or contradicts itself
3. CONSTRAINT: Violations of stated requirements or constraints
4. REASONING: Gaps in the reasoning chain or unsupported conclusions

Respond in JSON format:
{{"valid": true/false, "issues": [{{"type": "...", "severity": "info/warning/error/critical", "description": "...", "remediation": "..."}}], "confidence": 0.0-1.0}}"""

        user_prompt = f"""Context: {context}

Specialist {specialist} responded:
{response}

Validate this response critically. Be thorough but fair."""

        result_text = self._call_llm(system_prompt, user_prompt)

        try:
            result_data = json.loads(result_text)
            issues = [
                ValidationIssue(
                    issue_type=i.get('type', 'unknown'),
                    severity=i.get('severity', 'warning'),
                    description=i.get('description', ''),
                    specialist=specialist,
                    remediation=i.get('remediation')
                )
                for i in result_data.get('issues', [])
            ]

            return ValidationResult(
                is_valid=result_data.get('valid', True),
                validation_type=ValidationType.INTRA_AGENT,
                issues=issues,
                confidence=result_data.get('confidence', 0.8)
            )
        except json.JSONDecodeError:
            # If LLM didn't return valid JSON, assume valid but low confidence
            return ValidationResult(
                is_valid=True,
                validation_type=ValidationType.INTRA_AGENT,
                issues=[ValidationIssue(
                    issue_type='parse_error',
                    severity='warning',
                    description='Could not parse validation response'
                )],
                confidence=0.5
            )

    def validate_inter_agent(self, tx: Transaction) -> ValidationResult:
        """
        Validate consistency across all specialists in a transaction.
        Checks: dependency satisfaction, consistency, temporal ordering.
        """
        issues = []

        # Check 1: Dependency satisfaction
        for node, status in tx.s_d.nodes.items():
            if not tx.s_d.all_dependencies_satisfied(node):
                issues.append(ValidationIssue(
                    issue_type='dependency',
                    severity='error',
                    description=f"Dependencies for {node} not satisfied",
                    remediation=f"Ensure all dependencies of {node} complete first"
                ))

        # Check 2: Reasoning chain consistency
        if len(tx.s_o.reasoning_chains) > 1:
            # Look for contradictions
            for i, chain1 in enumerate(tx.s_o.reasoning_chains):
                for j, chain2 in enumerate(tx.s_o.reasoning_chains[i+1:], i+1):
                    # Simple contradiction check - could be more sophisticated
                    if 'REJECT' in chain1.upper() and 'APPROVE' in chain2.upper():
                        issues.append(ValidationIssue(
                            issue_type='consistency',
                            severity='warning',
                            description=f"Potential contradiction between reasoning {i} and {j}",
                            remediation="Reconcile opposing views in synthesis"
                        ))

        # Check 3: All specialists responded
        specialists_responded = set()
        for op in tx.s_o.operations:
            if op.get('type') == 'specialist_query':
                specialists_responded.add(op.get('specialist'))

        expected = {'crawdad', 'gecko', 'turtle', 'raven', 'spider', 'eagle_eye', 'peace_chief'}
        missing = expected - specialists_responded
        if missing:
            issues.append(ValidationIssue(
                issue_type='completeness',
                severity='error',
                description=f"Missing responses from: {', '.join(missing)}",
                remediation="Query missing specialists before proceeding"
            ))

        is_valid = not any(i.severity in ('error', 'critical') for i in issues)

        return ValidationResult(
            is_valid=is_valid,
            validation_type=ValidationType.INTER_AGENT,
            issues=issues,
            confidence=0.9 if is_valid else 0.6
        )


class SagaTransactionManager:
    """
    Manages multi-agent transactions with rollback capability.

    Follows the Saga pattern: each operation is paired with a
    compensating transaction that can undo it if needed.
    """

    def __init__(self, db_config: dict = None,
                 llm_endpoint: str = "http://100.116.27.89:8080/v1/chat/completions"):
        self.db_config = db_config or {
            'host': '100.112.254.96',
            'port': 5432,
            'database': 'zammad_production',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }
        self.validator = GlobalValidationAgent(llm_endpoint)
        self._compensation_handlers: Dict[str, Callable] = {}

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def register_compensation_handler(self, operation_type: str, handler: Callable):
        """Register a function to handle compensation for an operation type."""
        self._compensation_handlers[operation_type] = handler

    def begin_transaction(self, query_id: str, audit_hash: str,
                          query: str = "", domain: str = "general") -> Transaction:
        """
        Begin a new saga transaction.
        Creates checkpoint and returns transaction object.
        """
        tx = Transaction(
            query_id=query_id,
            audit_hash=audit_hash,
            status=TransactionStatus.PENDING
        )
        tx.s_a = ApplicationState(
            query=query,
            query_id=query_id,
            domain=domain
        )

        # Set up standard dependencies for Council deliberation
        specialists = ['crawdad', 'gecko', 'turtle', 'raven', 'spider', 'eagle_eye']
        for s in specialists:
            tx.s_d.add_dependency(s, 'peace_chief', 'requires')

        self._persist_checkpoint(tx)
        return tx

    def _persist_checkpoint(self, tx: Transaction):
        """Save transaction state to database."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO council_saga_transactions
                    (transaction_id, query_id, audit_hash, status,
                     s_a_state, s_o_state, s_d_state,
                     initiator, priority, max_retries, current_retry,
                     checkpoint_at, last_error, error_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
                    ON CONFLICT (transaction_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        s_a_state = EXCLUDED.s_a_state,
                        s_o_state = EXCLUDED.s_o_state,
                        s_d_state = EXCLUDED.s_d_state,
                        current_retry = EXCLUDED.current_retry,
                        checkpoint_at = NOW(),
                        last_error = EXCLUDED.last_error,
                        error_count = EXCLUDED.error_count
                """, (
                    tx.transaction_id,
                    tx.query_id,
                    tx.audit_hash,
                    tx.status.value,
                    Json(tx.s_a.to_dict()),
                    Json(tx.s_o.to_dict()),
                    Json(tx.s_d.to_dict()),
                    tx.initiator,
                    tx.priority,
                    tx.max_retries,
                    tx.current_retry,
                    tx.last_error,
                    tx.error_count
                ))
                conn.commit()
        finally:
            conn.close()

    def register_compensation(self, tx: Transaction, action: CompensatingAction, sequence: int):
        """Register a compensating action for potential rollback."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO council_compensation_registry
                    (transaction_id, sequence_num, operation_type,
                     operation_data, compensation_action)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    tx.transaction_id,
                    sequence,
                    action.operation_type,
                    Json({'specialist': action.specialist}),
                    Json(action.to_dict())
                ))
                conn.commit()
        finally:
            conn.close()

    def execute_operation(self, tx: Transaction, operation_type: str,
                          specialist: str, execute_fn: Callable,
                          compensation_data: dict = None) -> Tuple[bool, Any]:
        """
        Execute an operation with automatic compensation registration.

        Args:
            tx: Current transaction
            operation_type: Type of operation (e.g., 'specialist_query')
            specialist: Which specialist is performing this
            execute_fn: Function to execute (should return result or raise)
            compensation_data: Data needed for compensation

        Returns:
            Tuple of (success, result_or_error)
        """
        tx.status = TransactionStatus.EXECUTING
        sequence = len(tx.s_o.operations)

        # Register compensation BEFORE execution
        compensation = CompensatingAction(
            operation_type=operation_type,
            specialist=specialist,
            compensation_fn=f"compensate_{operation_type}",
            compensation_data=compensation_data or {}
        )
        self.register_compensation(tx, compensation, sequence)

        try:
            # Execute the operation
            result = execute_fn()

            # Record in operation log
            tx.s_o.append_operation(operation_type, specialist, {
                'success': True,
                'result_summary': str(result)[:200] if result else None
            })

            # Mark dependency as satisfied
            tx.s_d.mark_satisfied(specialist, True)

            # Checkpoint
            self._persist_checkpoint(tx)

            return True, result

        except Exception as e:
            tx.last_error = str(e)
            tx.error_count += 1
            tx.s_o.append_operation(operation_type, specialist, {
                'success': False,
                'error': str(e)
            })
            tx.s_d.mark_satisfied(specialist, False)
            self._persist_checkpoint(tx)

            return False, e

    def validate(self, tx: Transaction, specialist: str = None,
                 response: str = None) -> ValidationResult:
        """
        Run validation on transaction state.
        If specialist and response provided, runs intra-agent validation.
        Otherwise runs inter-agent validation.
        """
        tx.status = TransactionStatus.VALIDATING

        if specialist and response:
            result = self.validator.validate_intra_agent(
                specialist, response, tx.s_a.query
            )
        else:
            result = self.validator.validate_inter_agent(tx)

        # Store validation result
        self._store_validation_result(tx, result, specialist)

        return result

    def _store_validation_result(self, tx: Transaction, result: ValidationResult,
                                   specialist: str = None):
        """Store validation result to database."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO council_validation_results
                    (transaction_id, validation_type, target_specialist,
                     is_valid, confidence, issues)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    tx.transaction_id,
                    result.validation_type.value,
                    specialist,
                    result.is_valid,
                    result.confidence,
                    Json([i.to_dict() for i in result.issues])
                ))
                conn.commit()
        finally:
            conn.close()

    def commit(self, tx: Transaction):
        """Commit the transaction - mark as complete."""
        tx.status = TransactionStatus.COMMITTED
        tx.committed_at = datetime.now()

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE council_saga_transactions
                    SET status = 'committed', committed_at = NOW()
                    WHERE transaction_id = %s
                """, (tx.transaction_id,))
                conn.commit()
        finally:
            conn.close()

    def rollback(self, tx: Transaction) -> bool:
        """
        Rollback the transaction by executing compensating actions in reverse order.
        """
        tx.status = TransactionStatus.COMPENSATING

        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get compensations in reverse order
                cursor.execute("""
                    SELECT * FROM council_compensation_registry
                    WHERE transaction_id = %s AND NOT executed
                    ORDER BY sequence_num DESC
                """, (tx.transaction_id,))

                compensations = cursor.fetchall()

                all_success = True
                for comp in compensations:
                    try:
                        # Execute compensation
                        op_type = comp['operation_type']
                        if op_type in self._compensation_handlers:
                            handler = self._compensation_handlers[op_type]
                            handler(comp['compensation_action'])

                        # Mark as executed
                        cursor.execute("""
                            UPDATE council_compensation_registry
                            SET executed = TRUE, executed_at = NOW(),
                                execution_result = %s
                            WHERE compensation_id = %s
                        """, (Json({'success': True}), comp['compensation_id']))

                    except Exception as e:
                        cursor.execute("""
                            UPDATE council_compensation_registry
                            SET executed = TRUE, executed_at = NOW(),
                                execution_result = %s
                            WHERE compensation_id = %s
                        """, (Json({'success': False, 'error': str(e)}), comp['compensation_id']))
                        all_success = False

                # Update transaction status
                tx.status = TransactionStatus.ROLLED_BACK
                tx.rolled_back_at = datetime.now()
                cursor.execute("""
                    UPDATE council_saga_transactions
                    SET status = 'rolled_back', rolled_back_at = NOW()
                    WHERE transaction_id = %s
                """, (tx.transaction_id,))

                conn.commit()
                return all_success

        finally:
            conn.close()

    def can_retry(self, tx: Transaction) -> bool:
        """Check if transaction can be retried."""
        return tx.current_retry < tx.max_retries

    def retry(self, tx: Transaction) -> Transaction:
        """
        Create a retry transaction preserving valid portions of original.
        """
        tx.current_retry += 1

        # Reset to pending but keep learned information
        tx.status = TransactionStatus.PENDING

        # Keep successful operations, clear failed ones
        successful_ops = [
            op for op in tx.s_o.operations
            if op.get('data', {}).get('success', False)
        ]
        tx.s_o.operations = successful_ops

        # Clear validation issues
        tx.last_error = None

        self._persist_checkpoint(tx)
        return tx


# Convenience context manager
class SagaContext:
    """Context manager for saga transactions."""

    def __init__(self, manager: SagaTransactionManager, query_id: str,
                 audit_hash: str, query: str = ""):
        self.manager = manager
        self.query_id = query_id
        self.audit_hash = audit_hash
        self.query = query
        self.tx: Optional[Transaction] = None

    def __enter__(self) -> Transaction:
        self.tx = self.manager.begin_transaction(
            self.query_id, self.audit_hash, self.query
        )
        return self.tx

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Exception occurred - rollback
            if self.tx:
                self.manager.rollback(self.tx)
            return False

        # Check if we should commit or rollback
        if self.tx and self.tx.status != TransactionStatus.ROLLED_BACK:
            # Validate before commit
            validation = self.manager.validate(self.tx)
            if validation.is_valid:
                self.manager.commit(self.tx)
            else:
                self.manager.rollback(self.tx)

        return False


if __name__ == '__main__':
    import hashlib

    print("Testing SagaLLM Transaction Manager...")

    manager = SagaTransactionManager()

    # Create a test transaction
    test_query_id = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    test_hash = hashlib.md5(test_query_id.encode()).hexdigest()

    tx = manager.begin_transaction(
        query_id=test_query_id,
        audit_hash=test_hash,
        query="Should we implement feature X?",
        domain="engineering"
    )

    print(f"Created transaction: {tx.transaction_id}")
    print(f"Status: {tx.status.value}")

    # Simulate a specialist operation
    def mock_specialist_query():
        return "APPROVE - Feature X looks good technically."

    success, result = manager.execute_operation(
        tx=tx,
        operation_type='specialist_query',
        specialist='gecko',
        execute_fn=mock_specialist_query
    )

    print(f"Operation success: {success}")
    print(f"Result: {result}")

    # Validate
    validation = manager.validate(tx, 'gecko', result)
    print(f"Validation: valid={validation.is_valid}, confidence={validation.confidence}")

    if validation.issues:
        print("Issues found:")
        for issue in validation.issues:
            print(f"  - [{issue.severity}] {issue.description}")

    # For testing, commit the transaction
    manager.commit(tx)
    print(f"Final status: {tx.status.value}")
