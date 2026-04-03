from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.openai_client import OpenAIClient
from app.schemas.adjudications import AdjudicationSummary
from app.schemas.common import ConfidenceEnum
from app.schemas.evidence import EvidenceCandidate, EvidenceLabel


class AdjudicatorService:
    """Produces adjudication summary with explicit evidence-grounding language."""

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        self.openai = openai_client or OpenAIClient()

    async def adjudicate(self, normalized_claim: str, accepted: list[EvidenceCandidate], rejected: list[EvidenceCandidate]) -> AdjudicationSummary:
        if settings.openai_api_key:
            try:
                out = await self.openai.adjudicate(
                    {
                        "claim": normalized_claim,
                        "accepted_evidence": [e.model_dump(mode="json") for e in accepted],
                        "rejected_candidates": [e.model_dump(mode="json") for e in rejected],
                    }
                )
                return AdjudicationSummary(**out)
            except ProviderError:
                return self._mock_adjudication(normalized_claim, accepted, rejected)
        return self._mock_adjudication(normalized_claim, accepted, rejected)

    def _mock_adjudication(
        self, claim: str, accepted: list[EvidenceCandidate], rejected: list[EvidenceCandidate]
    ) -> AdjudicationSummary:
        direct_support = sum(1 for e in accepted if e.label == EvidenceLabel.direct_support)
        oppose = sum(1 for e in accepted if e.label == EvidenceLabel.opposing)
        alt = sum(1 for e in accepted if e.label == EvidenceLabel.alternative_contextual)

        if direct_support >= oppose + 2:
            confidence = ConfidenceEnum.medium
            conclusion = "Current retrieved evidence leans toward support, but remains conditional on study quality and context."
        elif oppose > direct_support:
            confidence = ConfidenceEnum.low
            conclusion = "Current retrieved evidence leans against the claim or indicates meaningful contradiction."
        else:
            confidence = ConfidenceEnum.low
            conclusion = "Retrieved evidence is mixed or weakly direct; no strong adjudication is justified."

        grounding_note = (
            "Evidence grounding is weak: few directly claim-bearing sources were accepted."
            if direct_support + oppose <= 1
            else "Evidence grounding is moderate: multiple claim-relevant sources were accepted."
        )

        return AdjudicationSummary(
            supporting_case=f"Accepted direct/indirect support items: {direct_support}.",
            opposing_case=f"Accepted opposing items: {oppose}.",
            alternative_explanations=f"Accepted alternative/contextual items: {alt}.",
            best_supported_conclusion=f"For claim '{claim}': {conclusion}",
            confidence=confidence,
            limitations=(
                f"{len(rejected)} candidates were filtered out; automated screening may miss nuanced evidence quality factors."
            ),
            reasoning_summary="Conclusion based on accepted-vs-rejected separation and directness-aware labeling.",
            evidence_grounding_note=grounding_note,
        )
