"""
Cherokee AI Federation — LLM Prompt Templates for Remediation

These prompts constrain Qwen 72B to generate ONLY template variable
values, NOT free-form YAML. The playbook structure comes from our
Jinja2 templates — the LLM just fills in the blanks.
"""

CLASSIFY_ALERT_PROMPT = """You are Eagle Eye, the monitoring specialist for the Cherokee AI Federation.
Classify this alert into exactly ONE category.

Alert content: {alert_content}
Alert severity: {severity}

Categories:
- service_down: A systemd service has stopped or is failing
- config_drift: A configuration file has changed unexpectedly
- resource_exhaustion: Disk, memory, or CPU is critically high
- database_issue: PostgreSQL connection or query failure
- network_issue: Connectivity between federation nodes is broken
- unknown: Cannot determine the issue

Respond with ONLY a JSON object:
{{"category": "<category>", "target_node": "<hostname or 'unknown'>", "target_service": "<service name or 'unknown'>", "summary": "<one line description>"}}
"""

FILL_TEMPLATE_PROMPT = """You are a remediation engine for the Cherokee AI Federation.
Given the alert classification below, provide ONLY the template variables needed
to fill the remediation playbook template.

Classification:
- Category: {category}
- Target node: {target_node}
- Target service: {target_service}
- Summary: {summary}

Similar past remediations from thermal memory:
{rag_context}

The playbook template expects these variables:
{template_variables}

CONSTRAINTS (Turtle's 7GEN Rule):
- Every value must be a simple string, list, or boolean
- No embedded Jinja2 or YAML in values
- No shell commands longer than 80 characters
- Service names must match known federation services
- File paths must start with /ganuda/ or /etc/

Respond with ONLY a JSON object containing the template variable values.
"""

# Known federation services for validation
KNOWN_SERVICES = {
    "redfin": [
        "vllm.service", "llm-gateway.service", "sag.service",
        "jr-queue-worker.service", "jr-bidding.service",
        "vetassist-frontend.service", "vetassist-backend.service",
        "telegram-chief.service",
    ],
    "bluefin": [
        "vlm-bluefin.service", "vlm-adapter.service",
        "yolo-world.service", "optic-nerve.service",
        "tribal-vision.service", "speed-detector.service",
    ],
    "greenfin": [
        "cherokee-embedding.service", "cherokee-thermal-purge.service",
        "promtail.service",
    ],
}