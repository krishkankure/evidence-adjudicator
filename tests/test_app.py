from fastapi.testclient import TestClient

from app.main import app
from app.providers.pubmed_client import PubMedClient
from app.services.query_generator import QueryGeneratorService


def test_health() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_get_claim() -> None:
    with TestClient(app) as client:
        create = client.post("/claims", json={"user_text": "Does vTSC2 correlate with mTORC1 downregulation?"})
        assert create.status_code == 200
        data = create.json()
        assert data["normalized_claim"] == "vTSC2 correlates with mTORC1 downregulation"

        get_resp = client.get(f"/claims/{data['claim_id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["claim_id"] == data["claim_id"]


def test_query_generator_deterministic() -> None:
    queries = QueryGeneratorService.generate("X is associated with Y")
    assert queries.support.endswith("evidence association mechanism")
    assert "contradictory evidence" in queries.oppose
    assert "alternative mechanism" in queries.alternative


async def _fake_search(self, query: str, retmax: int | None = None) -> list[dict]:  # noqa: ARG001
    return [
        {
            "pmid": "999",
            "title": f"Result for {query}",
            "authors": ["A B"],
            "journal": "J Test",
            "publication_year": 2022,
            "abstract": "Abstract snippet text for deterministic tests.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/999/",
        }
    ]


def test_pubmed_mock_behavior() -> None:
    import asyncio

    articles = asyncio.run(PubMedClient().search_articles("MOCK: query"))
    assert articles
    assert articles[0]["pmid"] == "12345678"


def test_pubmed_real_retrieval_returns_results() -> None:
    import asyncio

    # Use a broad, stable biomedical search term to avoid flaky empty-result responses.
    articles = asyncio.run(PubMedClient().search_articles("cancer", retmax=1))

    assert articles, "Expected at least one real PubMed result for query 'cancer'."
    article = articles[0]
    assert article["pmid"]
    assert article["title"]
    assert article["url"].startswith("https://pubmed.ncbi.nlm.nih.gov/")


def test_adjudication_flow(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(PubMedClient, "search_articles", _fake_search)
    with TestClient(app) as client:
        create = client.post("/claims", json={"user_text": "Is EGFR associated with response?"})
        claim_id = create.json()["claim_id"]

        adj = client.post(f"/claims/{claim_id}/adjudicate")
        assert adj.status_code == 200
        adj_id = adj.json()["adjudication_id"]

        detail = client.get(f"/adjudications/{adj_id}")
        assert detail.status_code == 200
        body = detail.json()
        assert set(body["evidence"].keys()) == {"supporting", "opposing", "alternative"}
        assert "adjudication" in body
        assert isinstance(body["citations"], list)

        ev = client.get(f"/adjudications/{adj_id}/evidence")
        assert ev.status_code == 200
        cit = client.get(f"/adjudications/{adj_id}/citations")
        assert cit.status_code == 200


def test_adjudication_flow_prints_inputs_outputs(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(PubMedClient, "search_articles", _fake_search)
    with TestClient(app) as client:
        claim_input = {"user_text": "Is KRAS associated with treatment response?"}
        print("INPUT /claims:", claim_input)
        create = client.post("/claims", json=claim_input)
        print("OUTPUT /claims:", create.status_code, create.json())
        assert create.status_code == 200
        claim_id = create.json()["claim_id"]

        adjudicate_path = f"/claims/{claim_id}/adjudicate"
        print("INPUT", adjudicate_path)
        adj = client.post(adjudicate_path)
        print("OUTPUT", adjudicate_path, ":", adj.status_code, adj.json())
        assert adj.status_code == 200
        adj_id = adj.json()["adjudication_id"]

        detail_path = f"/adjudications/{adj_id}"
        print("INPUT", detail_path)
        detail = client.get(detail_path)
        print("OUTPUT", detail_path, ":", detail.status_code, detail.json())
        assert detail.status_code == 200
