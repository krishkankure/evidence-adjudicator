import logging
import re
from dataclasses import dataclass

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.openai_client import OpenAIClient
from app.providers.pubmed_client import PubMedClient
from app.schemas.adjudications import GeneratedQueries
from app.schemas.evidence import Citation, EvidenceBundle, EvidenceCandidate, EvidenceDecision, EvidenceLabel
from app.utils.ids import new_id

logger = logging.getLogger(__name__)

STOPWORDS = {"does", "do", "is", "are", "was", "were", "the", "a", "an", "in", "on", "of", "to", "with", "for", "and", "or", "adult", "adults", "patient", "patients"}


@dataclass
class RetrievalResult:
    source_type: str
    query: str
    intent: str
    article: dict
    retrieval_score: float


class RetrievalBackend:
    source_type: str

    async def search(self, query: str, intent: str) -> list[RetrievalResult]:
        raise NotImplementedError


class PubMedRetrievalBackend(RetrievalBackend):
    source_type = "pubmed"

    def __init__(self, client: PubMedClient | None = None) -> None:
        self.client = client or PubMedClient()

    async def search(self, query: str, intent: str) -> list[RetrievalResult]:
        records = await self.client.search_articles(query)
        out: list[RetrievalResult] = []
        for idx, art in enumerate(records, start=1):
            out.append(
                RetrievalResult(
                    source_type=self.source_type,
                    query=query,
                    intent=intent,
                    article=art,
                    retrieval_score=max(0.0, 1.0 - 0.1 * (idx - 1)),
                )
            )
        return out




class OpenAIWebRetrievalBackend(RetrievalBackend):
    source_type = "web"

    def __init__(self, client: OpenAIClient | None = None) -> None:
        self.client = client or OpenAIClient()

    async def search(self, query: str, intent: str) -> list[RetrievalResult]:
        records = await self.client.web_search(query)
        out: list[RetrievalResult] = []
        for idx, art in enumerate(records, start=1):
            out.append(
                RetrievalResult(
                    source_type=self.source_type,
                    query=query,
                    intent=intent,
                    article=art,
                    retrieval_score=max(0.0, 0.85 - 0.1 * (idx - 1)),
                )
            )
        return out


class EvidencePipelineService:
    """Two-stage retrieval then directness-focused filtering for adjudication."""

    def __init__(self, backends: list[RetrievalBackend] | None = None) -> None:
        self.backends = backends or self._default_backends()

    def _default_backends(self) -> list[RetrievalBackend]:
        mode = (settings.retrieval_mode or "pubmed").lower()
        if mode == "web":
            return [OpenAIWebRetrievalBackend()]
        if mode == "hybrid":
            return [PubMedRetrievalBackend(), OpenAIWebRetrievalBackend()]
        return [PubMedRetrievalBackend()]

    async def run(self, claim: str, queries: GeneratedQueries) -> tuple[EvidenceBundle, list[Citation]]:
        raw: list[RetrievalResult] = []
        for q in queries.items:
            for backend in self.backends:
                try:
                    results = await backend.search(q.query, q.intent)
                except ProviderError as exc:
                    logger.warning(
                        "retrieval backend failure query=%s backend=%s error=%s",
                        q.query,
                        backend.source_type,
                        exc.message,
                    )
                    continue
                logger.info("retrieval query=%s backend=%s count=%s", q.query, backend.source_type, len(results))
                raw.extend(results)

        candidates = [self._to_candidate(claim, r) for r in raw]
        accepted = [c for c in candidates if c.decision == EvidenceDecision.accepted]
        rejected = [c for c in candidates if c.decision == EvidenceDecision.rejected]

        accepted = self._dedupe_best(accepted)
        rejected = self._dedupe_best(rejected)
        candidates = self._dedupe_best(candidates)

        accepted.sort(key=lambda x: x.final_score, reverse=True)
        rejected.sort(key=lambda x: x.final_score, reverse=True)
        candidates.sort(key=lambda x: x.final_score, reverse=True)

        bundle = EvidenceBundle(
            retrieved_candidates=candidates,
            accepted_evidence=accepted,
            rejected_candidates=rejected,
        )
        return bundle, self._to_citations(accepted)


    @staticmethod
    def _dedupe_best(items: list[EvidenceCandidate]) -> list[EvidenceCandidate]:
        by_key: dict[tuple[str | None, str], EvidenceCandidate] = {}
        for item in items:
            key = (item.pmid, item.title)
            prior = by_key.get(key)
            if prior is None or item.final_score > prior.final_score:
                by_key[key] = item
        return list(by_key.values())

    def _to_candidate(self, claim: str, raw: RetrievalResult) -> EvidenceCandidate:
        article = raw.article
        title = (article.get("title") or "Untitled").strip()
        abstract = (article.get("abstract") or "").strip()
        snippet = (abstract[:350] + "...") if len(abstract) > 350 else abstract
        finding = snippet[:160] if snippet else f"Evidence from title: {title[:130]}"

        directness, key_overlap = self._directness_score(claim, title, abstract)
        label = self._label_from_intent(raw.intent, directness, key_overlap)
        final_score = round(0.35 * raw.retrieval_score + 0.65 * directness, 4)

        accepted = label != EvidenceLabel.irrelevant and final_score >= 0.58 and key_overlap >= 1
        decision = EvidenceDecision.accepted if accepted else EvidenceDecision.rejected
        reason = self._decision_reason(label=label, directness=directness, decision=decision, key_overlap=key_overlap)

        pmid = article.get("pmid")
        url = article.get("url") or ""
        citation_link = url or (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid and raw.source_type == "pubmed" else "")

        return EvidenceCandidate(
            evidence_id=new_id("ev"),
            source_type=raw.source_type,
            query=raw.query,
            query_intent=raw.intent,
            pmid=pmid,
            title=title,
            abstract_snippet=snippet,
            authors=article.get("authors") or [],
            journal=article.get("journal") or "",
            publication_year=article.get("publication_year"),
            url=url,
            citation_link=citation_link,
            extracted_finding=finding,
            limitations_note="Automated ranking/filtering; verify study design and effect size manually.",
            retrieval_score=raw.retrieval_score,
            directness_score=directness,
            final_score=final_score,
            label=label,
            decision=decision,
            decision_reason=reason,
        )

    @staticmethod
    def _directness_score(claim: str, title: str, abstract: str) -> tuple[float, int]:
        claim_terms = [t.lower() for t in re.findall(r"[A-Za-z0-9\-]+", claim) if len(t) > 2 and t.lower() not in STOPWORDS]
        text_terms = {t.lower() for t in re.findall(r"[A-Za-z0-9\-]+", f"{title} {abstract}") if len(t) > 2}
        if not claim_terms:
            return 0.0, 0

        unique_claim = list(dict.fromkeys(claim_terms))
        overlap_terms = [t for t in unique_claim if t in text_terms]
        key_overlap = len(overlap_terms)
        overlap_ratio = key_overlap / max(1, len(unique_claim))

        strength_bonus = 0.0
        lowered = f"{title} {abstract}".lower()
        for token in ["systematic review", "meta-analysis", "randomized", "cohort", "mechanism", "replication", "triglyceride", "omega-3"]:
            if token in lowered:
                strength_bonus += 0.04

        return min(1.0, round(overlap_ratio + strength_bonus, 4)), key_overlap

    @staticmethod
    def _label_from_intent(intent: str, directness: float, key_overlap: int) -> EvidenceLabel:
        if directness < 0.3 or key_overlap == 0:
            return EvidenceLabel.irrelevant
        if intent == "direct_support":
            return EvidenceLabel.direct_support if directness >= 0.5 else EvidenceLabel.indirect_contextual_support
        if intent == "opposing":
            return EvidenceLabel.opposing
        if intent == "alternative_contextual":
            return EvidenceLabel.alternative_contextual
        return EvidenceLabel.indirect_contextual_support

    @staticmethod
    def _decision_reason(label: EvidenceLabel, directness: float, decision: EvidenceDecision, key_overlap: int) -> str:
        if decision == EvidenceDecision.rejected:
            if label == EvidenceLabel.irrelevant:
                return "Rejected: low claim-key-term overlap and weak direct relevance."
            return "Rejected: potentially relevant but below directness threshold for adjudication set."
        return f"Accepted: labeled {label.value} with directness score {directness:.2f} and key overlap {key_overlap}."

    def _to_citations(self, accepted: list[EvidenceCandidate]) -> list[Citation]:
        out: list[Citation] = []
        seen: set[tuple[str | None, str]] = set()
        for item in accepted:
            key = (item.pmid, item.title)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                Citation(
                    citation_id=new_id("cit"),
                    source_type=item.source_type,
                    pmid=item.pmid,
                    title=item.title,
                    journal=item.journal,
                    year=item.publication_year,
                    url=item.url,
                    citation_link=item.citation_link,
                    snippet=item.abstract_snippet[:180],
                )
            )
        return out
