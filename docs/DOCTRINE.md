# What Ganuda Does and Does Not Do

**Version**: 1.0
**Date**: December 14, 2025

---

## Identity Statement

**Ganuda Gateway is:**
> A private, cloud-optional AI inference and orchestration platform for environments where privacy, control, and autonomy matter.

---

## What Ganuda IS

### Core Capabilities (v1.0)

| Capability | Description |
|------------|-------------|
| **OpenAI-Compatible API** | Drop-in replacement for OpenAI client libraries |
| **Private Inference** | Run LLMs on your hardware, your network |
| **API Key Management** | Issue, revoke, and rate-limit access |
| **Audit Logging** | Track who accessed what, when |
| **Multi-Backend Support** | vLLM, Ollama, or external APIs |
| **Air-Gapped Operation** | Works completely offline |

### Target Users

- Development teams needing private LLM access
- Organizations with data sovereignty requirements
- Security-conscious builders
- Research labs and academic institutions
- Digital forensics and legal environments

### Design Principles

1. **Privacy by Default** - No telemetry, no phoning home
2. **Boring Reliability** - Works predictably, fails gracefully
3. **Single Config** - One YAML file controls everything
4. **Your Infrastructure** - Runs where you want it

---

## What Ganuda is NOT

### Not in Scope (v1.0)

| NOT This | Explanation |
|----------|-------------|
| **Consumer Assistant** | Not a chatbot product for end users |
| **AGI/Consciousness Project** | Not pursuing artificial general intelligence |
| **Autonomous Agent** | Does not take actions without explicit API calls |
| **Training Platform** | Does not train or fine-tune models |
| **Cloud Service** | Not a hosted SaaS offering |
| **Blockchain/Crypto** | No token, no chain, no Web3 |

### Explicit Exclusions

1. **No Autonomous Actions**
   - Ganuda only responds to API requests
   - Does not initiate actions on its own
   - Does not modify systems without explicit calls

2. **No Background Learning**
   - Does not learn from your queries
   - Does not improve models based on usage
   - Thermal Memory (optional) stores context, not training data

3. **No External Communication**
   - Does not send telemetry
   - Does not check for updates automatically
   - Does not beacon to any service

4. **No User Management**
   - API keys only, no user accounts
   - No authentication beyond API keys
   - No multi-user collaboration features

---

## Intelligence Modules (Optional)

These advanced features are **disabled by default** and require explicit opt-in:

| Module | What It Does | What It Does NOT Do |
|--------|--------------|---------------------|
| **Specialist Council** | Routes queries to domain experts | Make decisions without human approval |
| **Thermal Memory** | Maintains context across sessions | Train on your data |
| **Breadcrumb Trails** | Tracks decision reasoning | Share reasoning externally |
| **Query Triad** | Balances privacy/security concerns | Override your access controls |

Enable only what you need:
```yaml
modules:
  council_enabled: true   # Enable specific modules
  memory_enabled: false   # Keep others disabled
```

---

## Boundaries

### Ganuda Will:
- Process requests you send it
- Return responses from configured backends
- Log metadata for audit purposes
- Respect rate limits you configure
- Fail safely when backends are unavailable

### Ganuda Will NOT:
- Access systems beyond configured backends
- Store prompt or response content (unless you enable Memory)
- Make network connections you didn't configure
- Escalate privileges or bypass auth
- "Improve" itself without explicit updates

---

## Future Scope

Features under consideration for future versions:

- Role-based access control (RBAC)
- Multi-tenant isolation
- Federation between Ganuda instances
- Webhook notifications
- Custom model routing

These will be added deliberately, with documentation, and disabled by default.

---

## The Cherokee Principle

> "For Seven Generations"

Every feature decision considers long-term impact:
- Will this build trust or erode it?
- Does this add complexity users don't need?
- Can this be abused? How do we prevent it?

When in doubt, we leave it out.

---

## Questions?

If you're unsure whether Ganuda fits your use case:

1. Read the [Privacy Statement](PRIVACY.md)
2. Review the [Quickstart Guide](QUICKSTART.md)
3. Open an issue: https://github.com/cherokee-ai/ganuda/issues

---

*For Seven Generations - Cherokee AI Federation*
