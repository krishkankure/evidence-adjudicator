from app.schemas.adjudications import Queries


class QueryGeneratorService:
    """Deterministic query generator for adversarial retrieval branches."""

    @staticmethod
    def generate(normalized_claim: str) -> Queries:
        base = normalized_claim.strip()
        return Queries(
            support=f"{base} evidence association mechanism",
            oppose=f"{base} no association contradictory evidence failed replication",
            alternative=f"{base} alternative mechanism confounding context-specific explanation",
        )
