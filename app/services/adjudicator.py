from app.core.config import settings
from app.schemas.adjudications import AdjudicationSummary
from app.schemas.common import ConfidenceEnum
from app.schemas.evidence import EvidenceCard
from app.providers.openai_client import OpenAIClient


class AdjudicatorService:
    """Produces adjudication summary either via OpenAI or deterministic mock mode."""

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        self.openai = openai_client or OpenAIClient()

    async def adjudicate(
        self,
        normalized_claim: str,
        support: list[EvidenceCard],
        oppose: list[EvidenceCard],
        alternative: list[EvidenceCard],
    ) -> AdjudicationSummary:
        if settings.openai_api_key:
            out = await self.openai.adjudicate(
                {
                    "claim": normalized_claim,
                    "support": [e.model_dump() for e in support],
                    "oppose": [e.model_dump() for e in oppose],
                    "alternative": [e.model_dump() for e in alternative],
                }
            )
            return AdjudicationSummary(**out)
        return self._mock_adjudication(normalized_claim, support, oppose, alternative)

    def _mock_adjudication(
        self,
        claim: str,
        support: list[EvidenceCard],
        oppose: list[EvidenceCard],
        alternative: list[EvidenceCard],
    ) -> AdjudicationSummary:
        s, o, a = len(support), len(oppose), len(alternative)
        if s > o + 1:
            confidence = ConfidenceEnum.medium
        elif o > s:
            confidence = ConfidenceEnum.low
        else:
            confidence = ConfidenceEnum.low

        return AdjudicationSummary(
            supporting_case=f"Support branch returned {s} records. Top title: {support[0].title if support else 'none'}.",
            opposing_case=f"Oppose branch returned {o} records. Top title: {oppose[0].title if oppose else 'none'}.",
            alternative_explanations=f"Alternative branch returned {a} records suggesting context/mechanism confounding.",
            best_supported_conclusion=(
                f"MVP mock conclusion for '{claim}': evidence is mixed; review full citations before relying on this finding."
            ),
            confidence=confidence,
            limitations="Mock adjudicator mode; no model-based critical appraisal. Manual expert review required.",
            reasoning_summary="Counts and first-paper heuristics were used to balance supporting/opposing/alternative evidence.",
        )
