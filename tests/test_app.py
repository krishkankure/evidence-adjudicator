from fastapi.testclient import TestClient
import pytest

from app.core.exceptions import ProviderError
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


def test_pubmed_parsing_handles_nested_text_collective_author_and_medline_date() -> None:
    xml = """
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>111</PMID>
          <Article>
            <ArticleTitle>Study of <i>TP53</i> variants</ArticleTitle>
            <Journal>
              <Title>J Example</Title>
              <JournalIssue>
                <PubDate>
                  <MedlineDate>2021 Jan-Feb</MedlineDate>
                </PubDate>
              </JournalIssue>
            </Journal>
            <AuthorList>
              <Author>
                <CollectiveName>Genome Consortium</CollectiveName>
              </Author>
            </AuthorList>
            <Abstract>
              <AbstractText Label="BACKGROUND">A <i>nested</i> abstract.</AbstractText>
            </Abstract>
          </Article>
        </MedlineCitation>
      </PubmedArticle>
    </PubmedArticleSet>
    """

    articles = PubMedClient()._parse_efetch_xml(xml)
    assert len(articles) == 1
    assert articles[0]["title"] == "Study of TP53 variants"
    assert articles[0]["publication_year"] == 2021
    assert articles[0]["authors"] == ["Genome Consortium"]
    assert articles[0]["abstract"] == "A nested abstract."


def test_pubmed_invalid_xml_raises_provider_error(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import asyncio

    class _Resp:
        def __init__(self, payload: dict | None = None, text: str = "") -> None:
            self._payload = payload or {}
            self.text = text

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    class _DummyClient:
        async def __aenter__(self):  # type: ignore[no-untyped-def]
            return self

        async def __aexit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
            return False

        async def get(self, url, params):  # type: ignore[no-untyped-def]
            if "esearch.fcgi" in url:
                return _Resp({"esearchresult": {"idlist": ["123"]}})
            return _Resp(text="<not><xml>")

    monkeypatch.setattr("app.providers.pubmed_client.httpx.AsyncClient", lambda timeout=15.0: _DummyClient())

    with pytest.raises(ProviderError, match="PubMed XML parse failed"):
        asyncio.run(PubMedClient().search_articles("cancer", retmax=1))
