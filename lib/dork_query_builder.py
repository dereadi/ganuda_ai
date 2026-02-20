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