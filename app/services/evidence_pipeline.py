from app.providers.pubmed_client import PubMedClient
from app.schemas.common import BranchEnum
from app.schemas.evidence import Citation, EvidenceCard, GroupedEvidence
from app.utils.ids import new_id


class EvidencePipelineService:
    """Runs branch retrieval, normalizes evidence cards, and produces citations."""

    def __init__(self, pubmed_client: PubMedClient | None = None) -> None:
        self.pubmed = pubmed_client or PubMedClient()

    async def run(self, support_query: str, oppose_query: str, alternative_query: str) -> tuple[GroupedEvidence, list[Citation]]:
        support_articles = await self.pubmed.search_articles(support_query)
        oppose_articles = await self.pubmed.search_articles(oppose_query)
        alt_articles = await self.pubmed.search_articles(alternative_query)

        supporting = [self._to_card(a, BranchEnum.support, idx) for idx, a in enumerate(support_articles, start=1)]
        opposing = [self._to_card(a, BranchEnum.oppose, idx) for idx, a in enumerate(oppose_articles, start=1)]
        alternative = [self._to_card(a, BranchEnum.alternative, idx) for idx, a in enumerate(alt_articles, start=1)]

        grouped = GroupedEvidence(supporting=supporting, opposing=opposing, alternative=alternative)
        citations = self._to_citations(grouped)
        return grouped, citations

    def _to_card(self, article: dict, branch: BranchEnum, rank: int) -> EvidenceCard:
        snippet = (article.get("abstract") or "").strip()
        snippet = snippet[:350] + ("..." if len(snippet) > 350 else "")
        finding = snippet[:140] if snippet else f"Evidence from title: {article.get('title', '')[:120]}"
        return EvidenceCard(
            evidence_id=new_id("ev"),
            pmid=article.get("pmid"),
            title=article.get("title") or "Untitled",
            abstract_snippet=snippet,
            authors=article.get("authors") or [],
            journal=article.get("journal") or "",
            publication_year=article.get("publication_year"),
            query_branch=branch,
            relevance_score=max(0.1, 1.0 - (rank - 1) * 0.15),
            url=article.get("url") or "",
            extracted_finding=finding,
            limitation_note="MVP heuristic extraction; manual review recommended",
        )

    def _to_citations(self, grouped: GroupedEvidence) -> list[Citation]:
        citations: list[Citation] = []
        seen: set[tuple[str | None, str]] = set()
        for cards, branch in [
            (grouped.supporting, BranchEnum.support),
            (grouped.opposing, BranchEnum.oppose),
            (grouped.alternative, BranchEnum.alternative),
        ]:
            for card in cards:
                key = (card.pmid, branch.value)
                if key in seen:
                    continue
                seen.add(key)
                citations.append(
                    Citation(
                        citation_id=new_id("cit"),
                        pmid=card.pmid,
                        title=card.title,
                        journal=card.journal,
                        year=card.publication_year,
                        url=card.url,
                        quote_or_snippet=card.abstract_snippet[:180],
                        branch=branch,
                    )
                )
        return citations
