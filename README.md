# Evidence Adjudicator

A backend-first biomedical/scientific claim adjudication engine built with FastAPI.

## What this system now optimizes for
- **Evidence-grounded adjudication** (accepted evidence is separated from raw retrieval candidates).
- **Claim-direct retrieval** (query generation + directness reranking reduce topical-but-vague matches).
- **Traceability** (every accepted evidence item carries clickable citation metadata).
- **Extensibility** (retrieval backends are modular: `pubmed`, `web`, `hybrid` via config).

## Retrieval + adjudication pipeline (v2)
1. Parse + normalize claim.
2. Generate claim-specific scientific queries (support, contradiction, alternatives, replication).
3. Broad retrieval from configured backend(s):
   - PubMed (biomedical primary source)
   - optional web-assisted backend scaffold (OpenAI tool path)
4. Two-stage ranking/filtering:
   - retrieval score from backend rank
   - directness score from claim-term overlap + evidence-bearing study cues
5. Candidate labeling and decisioning:
   - `direct_support`
   - `indirect_contextual_support`
   - `opposing`
   - `alternative_contextual`
   - `irrelevant`
6. Accepted evidence is passed to adjudication; rejected candidates remain inspectable with rejection reasons.
7. Adjudication summary explicitly states evidence grounding strength and limitations.

## API response shape highlights
`GET /adjudications/{id}` now includes:
- `claim`
- `generated_queries`
- `evidence.retrieved_candidates`
- `evidence.accepted_evidence`
- `evidence.rejected_candidates`
- `adjudication`
- `citations`

Each evidence object includes:
- source metadata (PMID/title/journal/year/url)
- `citation_link`
- `label`, `decision`, `decision_reason`
- `retrieval_score`, `directness_score`, `final_score`
- extracted snippet/finding and limitations note

## Configuration
Environment variables (see `.env.example` and `app/core/config.py`):
- `RETRIEVAL_MODE=pubmed|web|hybrid` (default `pubmed`)
- `PUBMED_*` settings for NCBI retrieval
- `OPENAI_API_KEY` (for model adjudication and web-assisted retrieval path)

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
uvicorn app.main:app --reload
```

## Evaluation/testing hooks
- Unit/integration tests validate:
  - claim-specific query generation
  - adjudication response schema with accepted/rejected split
  - citation link presence
  - PubMed parser robustness for tricky XML cases

Run:
```bash
pytest
```

## Notes
- This system improves scientific rigor but does **not** replace expert review.
- High-stakes decisions require domain expert interpretation of primary literature.
