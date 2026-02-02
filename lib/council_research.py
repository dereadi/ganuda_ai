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