# Evidence Adjudicator (MVP Backend)

A backend-first biomedical evidence adjudication engine built with FastAPI.

## Why this is **not** a generic chatbot
This API is claim-centered: it explicitly retrieves and compares evidence from three adversarial branches before producing a conclusion:
1. supporting evidence
2. opposing/contradictory evidence
3. alternative explanations

The goal is to reduce framing bias and sycophancy in claim analysis.

## MVP capabilities
- Create and persist normalized biomedical claims
- Generate deterministic support/oppose/alternative queries
- Retrieve literature from PubMed (NCBI E-utilities)
- Build normalized evidence cards and citations
- Produce structured adjudication (OpenAI JSON mode if key exists; deterministic mock fallback otherwise)
- Frontend-friendly stable JSON contracts

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
uvicorn app.main:app --reload
```

## Sample curl commands
```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/claims \
  -H "Content-Type: application/json" \
  -d '{"user_text":"Does vTSC2 correlate with mTORC1 downregulation?"}'

curl -s -X POST http://127.0.0.1:8000/claims/<claim_id>/adjudicate

curl -s http://127.0.0.1:8000/adjudications/<adjudication_id>
curl -s http://127.0.0.1:8000/adjudications/<adjudication_id>/evidence
curl -s http://127.0.0.1:8000/adjudications/<adjudication_id>/citations
```

## Architecture (simple, extensible)
- `api/routers`: thin route handlers
- `services`: claim parsing, query generation, evidence pipeline, adjudicator
- `providers`: PubMed and OpenAI wrappers
- `repositories`: DB access
- `schemas`: stable API contracts
- `models`: SQLite persistence (claims + adjudications)

## Example response (adjudication detail)
Returns:
- grouped evidence (`supporting`, `opposing`, `alternative`)
- adjudication summary (`best_supported_conclusion`, `confidence`, limitations)
- normalized citations list

## Testing
```bash
pytest
```

## Notes
- This is an MVP for adjudicating public literature claims.
- Not medical advice.
- Manual domain expert review is required for high-stakes decisions.

## TODO / next steps
- Background jobs for async adjudication execution
- Embeddings + vector retrieval
- Reranking and relevance scoring improvements
- React/Next.js frontend integration
- Auth / multi-user tenancy
- Better evidence extraction and critical appraisal
- Streaming adjudication updates
- Additional literature sources beyond PubMed
