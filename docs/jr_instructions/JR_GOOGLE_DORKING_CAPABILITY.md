# Jr Instructions: Google Dorking Capability for Tribe Research

**Priority**: 2
**Assigned Jr**: it_triad_jr
**Purpose**: Enhance Tribe's web research with advanced search operators

---

## OBJECTIVE

Add Google dorking (advanced search operators) capability to the Tribe's research toolkit. This enables precise, targeted searches for:
- Specific file types (PDFs, configs, code)
- Domain-specific content
- Exposed information and documentation
- Academic papers and technical resources

---

## BACKGROUND

Google dorks are special search operators that refine queries:

| Operator | Purpose | Example |
|----------|---------|---------|
| `site:` | Limit to domain | `site:github.com vllm` |
| `filetype:` | Find file types | `filetype:pdf transformer architecture` |
| `intitle:` | Words in title | `intitle:configuration kubernetes` |
| `inurl:` | Words in URL | `inurl:api documentation` |
| `"exact phrase"` | Exact match | `"multi-agent system"` |
| `-exclude` | Exclude terms | `python tutorial -beginner` |
| `OR` | Either term | `vLLM OR TensorRT` |
| `*` | Wildcard | `how to * kubernetes` |
| `before:` / `after:` | Date range | `after:2024-01-01 LLM scaling` |
| `related:` | Similar sites | `related:arxiv.org` |
| `cache:` | Cached version | `cache:example.com` |

---

### Task 1: Create Dork Query Builder

Create `/ganuda/lib/dork_query_builder.py`:

```python
#!/usr/bin/env python3
"""
Google Dork Query Builder
Cherokee AI Federation - For Seven Generations

Constructs advanced search queries for targeted research.
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class FileType(Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    XLS = "xls"
    XLSX = "xlsx"
    PPT = "ppt"
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    YAML = "yaml"
    YML = "yml"
    XML = "xml"
    MD = "md"
    PY = "py"
    JS = "js"
    SQL = "sql"
    LOG = "log"
    CONF = "conf"
    ENV = "env"


@dataclass
class DorkQuery:
    """Represents a constructed dork query."""
    query: str
    purpose: str
    operators_used: List[str]

    def __str__(self):
        return self.query


class DorkQueryBuilder:
    """Build advanced Google search queries."""

    def __init__(self):
        self.parts = []
        self.operators = []

    def reset(self):
        """Reset the builder for a new query."""
        self.parts = []
        self.operators = []
        return self

    def keywords(self, *terms: str) -> 'DorkQueryBuilder':
        """Add search keywords."""
        for term in terms:
            if ' ' in term:
                self.parts.append(f'"{term}"')
            else:
                self.parts.append(term)
        return self

    def exact(self, phrase: str) -> 'DorkQueryBuilder':
        """Add exact phrase match."""
        self.parts.append(f'"{phrase}"')
        self.operators.append('exact')
        return self

    def site(self, domain: str) -> 'DorkQueryBuilder':
        """Limit search to specific domain."""
        self.parts.append(f'site:{domain}')
        self.operators.append('site')
        return self

    def filetype(self, ft: FileType) -> 'DorkQueryBuilder':
        """Search for specific file type."""
        self.parts.append(f'filetype:{ft.value}')
        self.operators.append('filetype')
        return self

    def intitle(self, term: str) -> 'DorkQueryBuilder':
        """Term must appear in page title."""
        self.parts.append(f'intitle:{term}')
        self.operators.append('intitle')
        return self

    def inurl(self, term: str) -> 'DorkQueryBuilder':
        """Term must appear in URL."""
        self.parts.append(f'inurl:{term}')
        self.operators.append('inurl')
        return self

    def intext(self, term: str) -> 'DorkQueryBuilder':
        """Term must appear in page body."""
        self.parts.append(f'intext:{term}')
        self.operators.append('intext')
        return self

    def exclude(self, term: str) -> 'DorkQueryBuilder':
        """Exclude pages with this term."""
        self.parts.append(f'-{term}')
        self.operators.append('exclude')
        return self

    def exclude_site(self, domain: str) -> 'DorkQueryBuilder':
        """Exclude specific domain."""
        self.parts.append(f'-site:{domain}')
        self.operators.append('exclude_site')
        return self

    def or_terms(self, *terms: str) -> 'DorkQueryBuilder':
        """Any of these terms (OR logic)."""
        or_clause = ' OR '.join(terms)
        self.parts.append(f'({or_clause})')
        self.operators.append('or')
        return self

    def date_range(self, after: Optional[str] = None,
                   before: Optional[str] = None) -> 'DorkQueryBuilder':
        """Filter by date (YYYY-MM-DD format)."""
        if after:
            self.parts.append(f'after:{after}')
        if before:
            self.parts.append(f'before:{before}')
        self.operators.append('date')
        return self

    def related(self, url: str) -> 'DorkQueryBuilder':
        """Find sites related to URL."""
        self.parts.append(f'related:{url}')
        self.operators.append('related')
        return self

    def build(self, purpose: str = "") -> DorkQuery:
        """Build the final query."""
        return DorkQuery(
            query=' '.join(self.parts),
            purpose=purpose,
            operators_used=list(set(self.operators))
        )


# Pre-built research queries for common use cases
class ResearchDorks:
    """Common research query patterns."""

    @staticmethod
    def arxiv_papers(topic: str, year: int = 2024) -> DorkQuery:
        """Find arxiv papers on topic."""
        return (DorkQueryBuilder()
                .site('arxiv.org')
                .keywords(topic)
                .date_range(after=f'{year}-01-01')
                .build(f"Arxiv papers on {topic} since {year}"))

    @staticmethod
    def github_repos(topic: str, language: Optional[str] = None) -> DorkQuery:
        """Find GitHub repositories."""
        builder = DorkQueryBuilder().site('github.com').keywords(topic)
        if language:
            builder.keywords(language)
        return builder.build(f"GitHub repos for {topic}")

    @staticmethod
    def technical_docs(product: str, doc_type: str = "documentation") -> DorkQuery:
        """Find technical documentation."""
        return (DorkQueryBuilder()
                .keywords(product, doc_type)
                .or_terms('docs', 'documentation', 'guide', 'manual')
                .filetype(FileType.PDF)
                .build(f"Technical docs for {product}"))

    @staticmethod
    def config_examples(technology: str) -> DorkQuery:
        """Find configuration examples."""
        return (DorkQueryBuilder()
                .keywords(technology, 'config', 'example')
                .or_terms('yaml', 'json', 'toml', 'conf')
                .exclude('error')
                .build(f"Config examples for {technology}"))

    @staticmethod
    def api_documentation(service: str) -> DorkQuery:
        """Find API documentation."""
        return (DorkQueryBuilder()
                .keywords(service, 'API')
                .or_terms('documentation', 'reference', 'endpoints')
                .inurl('api')
                .build(f"API docs for {service}"))

    @staticmethod
    def security_advisories(product: str) -> DorkQuery:
        """Find security advisories."""
        return (DorkQueryBuilder()
                .keywords(product)
                .or_terms('CVE', 'vulnerability', 'security advisory', 'exploit')
                .exclude_site('twitter.com')
                .exclude_site('reddit.com')
                .build(f"Security advisories for {product}"))

    @staticmethod
    def job_postings(role: str, remote: bool = True) -> DorkQuery:
        """Find job postings."""
        builder = (DorkQueryBuilder()
                   .keywords(role)
                   .or_terms('hiring', 'job', 'position', 'opening'))
        if remote:
            builder.keywords('remote')
        return builder.exclude_site('linkedin.com').build(f"Job postings for {role}")

    @staticmethod
    def research_papers(topic: str, conference: Optional[str] = None) -> DorkQuery:
        """Find research papers."""
        builder = (DorkQueryBuilder()
                   .keywords(topic)
                   .filetype(FileType.PDF)
                   .or_terms('paper', 'research', 'study', 'analysis'))
        if conference:
            builder.keywords(conference)
        return builder.build(f"Research papers on {topic}")


class IoTDorks:
    """IoT device research queries."""

    @staticmethod
    def device_manual(vendor: str, model: str = "") -> DorkQuery:
        """Find device manual/documentation."""
        builder = DorkQueryBuilder().keywords(vendor)
        if model:
            builder.keywords(model)
        return (builder
                .or_terms('manual', 'user guide', 'documentation', 'datasheet')
                .filetype(FileType.PDF)
                .build(f"Manual for {vendor} {model}"))

    @staticmethod
    def firmware_info(vendor: str, model: str = "") -> DorkQuery:
        """Find firmware downloads and changelogs."""
        builder = DorkQueryBuilder().keywords(vendor)
        if model:
            builder.keywords(model)
        return (builder
                .or_terms('firmware', 'update', 'download', 'changelog', 'release notes')
                .build(f"Firmware for {vendor} {model}"))

    @staticmethod
    def default_credentials(vendor: str) -> DorkQuery:
        """Find default credentials (for security audit)."""
        return (DorkQueryBuilder()
                .keywords(vendor)
                .or_terms('default password', 'default credentials', 'factory password', 'default login')
                .exclude_site('twitter.com')
                .exclude_site('facebook.com')
                .build(f"Default credentials for {vendor}"))

    @staticmethod
    def api_integration(vendor: str, model: str = "") -> DorkQuery:
        """Find API/integration documentation."""
        builder = DorkQueryBuilder().keywords(vendor)
        if model:
            builder.keywords(model)
        return (builder
                .or_terms('API', 'REST', 'integration', 'home assistant', 'MQTT', 'SDK')
                .build(f"API integration for {vendor} {model}"))

    @staticmethod
    def security_vulnerabilities(vendor: str, model: str = "") -> DorkQuery:
        """Find known security issues."""
        builder = DorkQueryBuilder().keywords(vendor)
        if model:
            builder.keywords(model)
        return (builder
                .or_terms('CVE', 'vulnerability', 'exploit', 'security advisory', 'hack')
                .exclude_site('twitter.com')
                .build(f"Security issues for {vendor} {model}"))

    @staticmethod
    def management_interface(vendor: str) -> DorkQuery:
        """Find management interface documentation."""
        return (DorkQueryBuilder()
                .keywords(vendor, 'admin')
                .or_terms('web interface', 'management', 'configuration', 'setup', 'admin panel')
                .build(f"Management interface for {vendor}"))

    @staticmethod
    def protocol_docs(protocol: str) -> DorkQuery:
        """Find protocol documentation (MQTT, Zigbee, Z-Wave, etc)."""
        return (DorkQueryBuilder()
                .keywords(protocol)
                .or_terms('specification', 'protocol', 'documentation', 'reference')
                .filetype(FileType.PDF)
                .build(f"Protocol docs for {protocol}"))

    @staticmethod
    def home_assistant_integration(device: str) -> DorkQuery:
        """Find Home Assistant integration info."""
        return (DorkQueryBuilder()
                .site('home-assistant.io')
                .keywords(device)
                .build(f"Home Assistant integration for {device}"))

    @staticmethod
    def teardown_specs(vendor: str, model: str = "") -> DorkQuery:
        """Find teardowns and hardware specs."""
        builder = DorkQueryBuilder().keywords(vendor)
        if model:
            builder.keywords(model)
        return (builder
                .or_terms('teardown', 'hardware', 'specs', 'chipset', 'FCC', 'iFixit')
                .build(f"Hardware specs for {vendor} {model}"))


# Device-specific research for known vendors
class VendorDorks:
    """Vendor-specific research helpers."""

    @staticmethod
    def sonos(query_type: str = "api") -> DorkQuery:
        """Sonos-specific research."""
        base = DorkQueryBuilder().keywords('Sonos')
        if query_type == "api":
            return base.or_terms('API', 'control', 'SOAP', 'UPnP').build("Sonos API docs")
        elif query_type == "security":
            return base.or_terms('CVE', 'vulnerability', 'exploit').build("Sonos security")
        elif query_type == "integration":
            return base.site('home-assistant.io').build("Sonos Home Assistant")
        return base.build("Sonos general")

    @staticmethod
    def espressif(query_type: str = "docs") -> DorkQuery:
        """ESP32/ESP8266 research."""
        base = DorkQueryBuilder().or_terms('ESP32', 'ESP8266', 'Espressif')
        if query_type == "docs":
            return base.site('docs.espressif.com').build("Espressif official docs")
        elif query_type == "arduino":
            return base.keywords('Arduino', 'library').build("ESP Arduino libraries")
        elif query_type == "security":
            return base.or_terms('vulnerability', 'exploit', 'flash dump').build("ESP security")
        return base.build("Espressif general")

    @staticmethod
    def daikin(query_type: str = "api") -> DorkQuery:
        """Daikin HVAC research."""
        base = DorkQueryBuilder().keywords('Daikin')
        if query_type == "api":
            return base.or_terms('API', 'BRP', 'wifi', 'control', 'protocol').build("Daikin API")
        elif query_type == "integration":
            return base.or_terms('Home Assistant', 'daikin_ac', 'MQTT').build("Daikin integration")
        return base.build("Daikin general")

    @staticmethod
    def amazon_echo(query_type: str = "api") -> DorkQuery:
        """Amazon Echo/Alexa research."""
        base = DorkQueryBuilder().or_terms('Echo', 'Alexa', 'Fire TV')
        if query_type == "api":
            return base.or_terms('API', 'skill', 'developer').site('developer.amazon.com').build("Alexa API")
        elif query_type == "security":
            return base.or_terms('vulnerability', 'privacy', 'exploit').build("Echo security")
        return base.build("Amazon Echo general")

    @staticmethod
    def cisco_linksys(query_type: str = "admin") -> DorkQuery:
        """Cisco/Linksys router research."""
        base = DorkQueryBuilder().or_terms('Cisco', 'Linksys')
        if query_type == "admin":
            return base.or_terms('admin', 'default password', 'web interface', 'firmware').build("Router admin")
        elif query_type == "security":
            return base.or_terms('CVE', 'vulnerability', 'exploit', 'backdoor').build("Router security")
        return base.build("Cisco/Linksys general")


if __name__ == '__main__':
    # Demo queries
    print("=== Dork Query Examples ===\n")

    # Custom query
    q = (DorkQueryBuilder()
         .keywords('multi-agent', 'LLM')
         .site('arxiv.org')
         .filetype(FileType.PDF)
         .date_range(after='2024-06-01')
         .build("Recent multi-agent LLM papers"))
    print(f"Custom: {q.query}")
    print(f"Purpose: {q.purpose}\n")

    # Pre-built queries
    print(f"Arxiv: {ResearchDorks.arxiv_papers('recursive transformer')}")
    print(f"GitHub: {ResearchDorks.github_repos('vllm', 'python')}")
    print(f"Docs: {ResearchDorks.technical_docs('kubernetes')}")
    print(f"Security: {ResearchDorks.security_advisories('postgresql')}")
    print(f"Jobs: {ResearchDorks.job_postings('AI engineer', remote=True)}")
```

---

### Task 2: Integrate with Web Research Module

Update `/ganuda/jr_executor/web_research.py` to use dorks:

```python
# Add to web_research.py

from dork_query_builder import DorkQueryBuilder, ResearchDorks, FileType

def research_with_dorks(topic: str, research_type: str = "general") -> dict:
    """
    Research using appropriate dork queries.

    Args:
        topic: What to research
        research_type: One of: papers, github, docs, security, jobs, config

    Returns:
        Dict with query used and results
    """
    dork_map = {
        "papers": ResearchDorks.arxiv_papers,
        "github": ResearchDorks.github_repos,
        "docs": ResearchDorks.technical_docs,
        "security": ResearchDorks.security_advisories,
        "jobs": ResearchDorks.job_postings,
        "config": ResearchDorks.config_examples,
    }

    if research_type in dork_map:
        query = dork_map[research_type](topic)
    else:
        # General research
        query = (DorkQueryBuilder()
                 .keywords(topic)
                 .exclude_site('pinterest.com')
                 .exclude_site('facebook.com')
                 .build(f"General research on {topic}"))

    # Use existing fetch mechanism with dork query
    results = web_search(query.query)

    return {
        "query": query.query,
        "purpose": query.purpose,
        "operators": query.operators_used,
        "results": results
    }
```

---

### Task 3: Add Council Research Helper

Create `/ganuda/lib/council_research.py`:

```python
#!/usr/bin/env python3
"""
Council Research Helper
Uses dorking for specialist research needs.
"""

from dork_query_builder import DorkQueryBuilder, ResearchDorks, FileType


def specialist_research_queries(specialist: str, topic: str) -> list:
    """
    Generate research queries tailored to specialist perspective.

    Each specialist has different research priorities.
    """
    queries = []

    if specialist == 'gecko':
        # Technical/performance focus
        queries.append(ResearchDorks.github_repos(topic))
        queries.append(ResearchDorks.technical_docs(topic))
        queries.append((DorkQueryBuilder()
                        .keywords(topic, 'benchmark', 'performance')
                        .build("Performance benchmarks")))

    elif specialist == 'crawdad':
        # Security focus
        queries.append(ResearchDorks.security_advisories(topic))
        queries.append((DorkQueryBuilder()
                        .keywords(topic)
                        .or_terms('CVE', 'OWASP', 'vulnerability', 'patch')
                        .site('nvd.nist.gov')
                        .build("NVD security database")))

    elif specialist == 'turtle':
        # Long-term/sustainability focus
        queries.append((DorkQueryBuilder()
                        .keywords(topic, 'sustainability', 'long-term')
                        .or_terms('impact', 'future', 'legacy')
                        .build("Long-term impact analysis")))
        queries.append(ResearchDorks.research_papers(topic))

    elif specialist == 'eagle_eye':
        # Monitoring/observability focus
        queries.append((DorkQueryBuilder()
                        .keywords(topic, 'monitoring')
                        .or_terms('metrics', 'observability', 'logging', 'tracing')
                        .build("Monitoring solutions")))
        queries.append(ResearchDorks.config_examples(f"{topic} prometheus"))

    elif specialist == 'spider':
        # Integration/cultural focus
        queries.append((DorkQueryBuilder()
                        .keywords(topic, 'integration')
                        .or_terms('API', 'SDK', 'connector', 'plugin')
                        .build("Integration options")))

    elif specialist == 'raven':
        # Strategic focus
        queries.append((DorkQueryBuilder()
                        .keywords(topic, 'strategy')
                        .or_terms('roadmap', 'architecture', 'design')
                        .filetype(FileType.PDF)
                        .build("Strategic documents")))
        queries.append(ResearchDorks.arxiv_papers(topic))

    else:
        # Default: general research
        queries.append(ResearchDorks.research_papers(topic))
        queries.append(ResearchDorks.github_repos(topic))

    return queries


if __name__ == '__main__':
    # Example: what would each specialist research for "vLLM"?
    topic = "vLLM inference"

    for specialist in ['gecko', 'crawdad', 'turtle', 'eagle_eye', 'spider', 'raven']:
        print(f"\n=== {specialist.upper()} ===")
        for q in specialist_research_queries(specialist, topic):
            print(f"  {q.purpose}: {q.query}")
```

---

### Task 4: Store Dork Patterns in Thermal Memory

Create SQL to store useful dork patterns:

```sql
-- /ganuda/sql/dork_patterns.sql

CREATE TABLE IF NOT EXISTS dork_patterns (
    id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(64) NOT NULL,
    query_template TEXT NOT NULL,
    use_case TEXT,
    specialist_affinity VARCHAR(32),
    success_count INT DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed with useful patterns
INSERT INTO dork_patterns (pattern_name, query_template, use_case, specialist_affinity) VALUES
('arxiv_recent', 'site:arxiv.org {topic} after:{year}-01-01', 'Find recent papers', 'raven'),
('github_python', 'site:github.com {topic} language:python', 'Python repos', 'gecko'),
('security_cve', '{product} (CVE OR vulnerability OR exploit) -site:twitter.com', 'Security issues', 'crawdad'),
('config_yaml', '{tech} config example (yaml OR yml) -error', 'Config examples', 'eagle_eye'),
('api_docs', '{service} API (documentation OR reference) inurl:api', 'API documentation', 'spider'),
('benchmark', '{topic} benchmark performance comparison', 'Performance data', 'gecko'),
('integration', '{product} integration (plugin OR connector OR SDK)', 'Integration options', 'spider'),
('long_term', '{topic} (sustainability OR "long term" OR legacy OR future)', '7Gen analysis', 'turtle')
ON CONFLICT DO NOTHING;
```

---

## SUCCESS CRITERIA

1. `dork_query_builder.py` created with fluent API
2. `ResearchDorks` class provides common patterns
3. `council_research.py` tailors queries to specialist perspectives
4. Integration with existing web_research module
5. Dork patterns stored in database for reuse/learning

---

## EXAMPLE USAGE

```python
# Find recent multi-agent papers
query = (DorkQueryBuilder()
         .keywords("multi-agent", "LLM")
         .site("arxiv.org")
         .date_range(after="2024-06-01")
         .filetype(FileType.PDF)
         .build("Recent multi-agent papers"))

print(query)
# Output: "multi-agent" LLM site:arxiv.org after:2024-06-01 filetype:pdf

# Security research for Crawdad
queries = specialist_research_queries("crawdad", "postgresql")
# Returns CVE searches, NVD queries, vulnerability scans
```

---

*For Seven Generations - Cherokee AI Federation*
