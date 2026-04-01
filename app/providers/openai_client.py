import json

import httpx

from app.core.config import settings
from app.core.exceptions import ProviderError


class OpenAIClient:
    def __init__(self) -> None:
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model

    async def adjudicate(self, payload: dict) -> dict:
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY missing")

        system_prompt = (
            "You are a biomedical evidence adjudicator. Do not assume the user claim is true. "
            "Do not be sycophantic. Weigh evidence quality/directness/specificity. Distinguish contradiction, "
            "lack of evidence, and alternatives. Be concise and neutral. Do not reveal chain-of-thought. "
            "Output only valid JSON with the requested fields."
        )

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "input": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(payload)},
                    ],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "adjudication",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "supporting_case": {"type": "string"},
                                    "opposing_case": {"type": "string"},
                                    "alternative_explanations": {"type": "string"},
                                    "best_supported_conclusion": {"type": "string"},
                                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                                    "limitations": {"type": "string"},
                                    "reasoning_summary": {"type": "string"},
                                },
                                "required": [
                                    "supporting_case",
                                    "opposing_case",
                                    "alternative_explanations",
                                    "best_supported_conclusion",
                                    "confidence",
                                    "limitations",
                                    "reasoning_summary",
                                ],
                                "additionalProperties": False,
                            },
                        }
                    },
                },
            )
            if resp.status_code >= 400:
                raise ProviderError(f"OpenAI API error: {resp.text}")
            data = resp.json()
            text = data.get("output", [{}])[0].get("content", [{}])[0].get("text", "{}")
            return json.loads(text)
