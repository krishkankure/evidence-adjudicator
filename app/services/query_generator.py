import re

from app.schemas.adjudications import GeneratedQueries, GeneratedQuery


class QueryGeneratorService:
    """Claim-aware query generation for biomedical retrieval."""

    STOPWORDS = {
        "does",
        "do",
        "is",
        "are",
        "was",
        "were",
        "the",
        "a",
        "an",
        "in",
        "on",
        "of",
        "to",
        "with",
        "for",
        "and",
        "or",
        "adults",
        "adult",
        "patients",
        "patient",
        "associated",
        "associate",
        "reduce",
        "reduces",
        "increase",
        "increases",
    }

    @staticmethod
    def generate(normalized_claim: str) -> GeneratedQueries:
        keys = QueryGeneratorService._key_terms(normalized_claim)
        core = QueryGeneratorService._pubmed_core(keys)
        claim_text = normalized_claim.strip()

        queries = [
            GeneratedQuery(
                query=(
                    f"({core}) AND "
                    "(systematic review[Title/Abstract] OR meta-analysis[Title/Abstract] OR mechanism[Title/Abstract])"
                ),
                intent="direct_support",
            ),
            GeneratedQuery(
                query=(
                    f"({core}) AND "
                    "(randomized[Title/Abstract] OR trial[Title/Abstract] OR cohort[Title/Abstract]) AND "
                    "(contradictory[Title/Abstract] OR null[Title/Abstract] OR no association[Title/Abstract])"
                ),
                intent="opposing",
            ),
            GeneratedQuery(
                query=(
                    f"({core}) AND "
                    "(confounding[Title/Abstract] OR bias[Title/Abstract] OR subgroup[Title/Abstract] "
                    "OR context-specific[Title/Abstract] OR alternative explanation[Title/Abstract])"
                ),
                intent="alternative_contextual",
            ),
            GeneratedQuery(
                query=(
                    f"({core}) AND "
                    "(replication[Title/Abstract] OR failed replication[Title/Abstract] OR reproducibility[Title/Abstract])"
                ),
                intent="opposing",
            ),
            GeneratedQuery(
                query=f'"{claim_text}"[Title/Abstract]',
                intent="direct_support",
            ),
        ]
        return GeneratedQueries(items=queries)

    @staticmethod
    def _key_terms(claim: str) -> list[str]:
        tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9\-]+", claim) if len(t) > 2]
        filtered = [t for t in tokens if t not in QueryGeneratorService.STOPWORDS]
        # Keep unique order and prefer first biologically-relevant terms appearing in the claim.
        uniq: list[str] = []
        for t in filtered:
            if t not in uniq:
                uniq.append(t)
        return uniq[:4] if uniq else tokens[:3]

    @staticmethod
    def _pubmed_core(terms: list[str]) -> str:
        if not terms:
            return ""
        if len(terms) == 1:
            return f'"{terms[0]}"[Title/Abstract]'
        return " AND ".join(f'"{t}"[Title/Abstract]' for t in terms)
