import asyncio

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


def test_query_generator_claim_specific() -> None:
    queries = QueryGeneratorService.generate("X is associated with Y")
    assert len(queries.items) >= 5
    assert any(q.intent == "direct_support" for q in queries.items)
    assert any("[Title/Abstract]" in q.query for q in queries.items)
    assert any("replication" in q.query for q in queries.items)


async def _fake_search(self, query: str, retmax: int | None = None) -> list[dict]:  # noqa: ARG001
    return [
        {
            "pmid": "999",
            "title": f"Systematic review result for {query}",
            "authors": ["A B"],
            "journal": "J Test",
            "publication_year": 2022,
            "abstract": "This study evaluates direct association, mechanism, and contradictory findings.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/999/",
        }
    ]


def test_pubmed_mock_behavior() -> None:
    articles = asyncio.run(PubMedClient().search_articles("MOCK: query"))
    assert articles
    assert articles[0]["pmid"] == "12345678"


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
        assert "generated_queries" in body
        assert set(body["evidence"].keys()) == {"retrieved_candidates", "accepted_evidence", "rejected_candidates"}
        assert isinstance(body["citations"], list)
        assert body["adjudication"]["evidence_grounding_note"]

        accepted = body["evidence"]["accepted_evidence"]
        assert accepted
        assert accepted[0]["decision"] == "accepted"
        assert accepted[0]["citation_link"].startswith("https://pubmed.ncbi.nlm.nih.gov/")


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


def test_directness_filter_rejects_tangential_evidence(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def _mixed_search(self, query: str, retmax: int | None = None) -> list[dict]:  # noqa: ARG001
        return [
            {
                "pmid": "1",
                "title": "Omega-3 supplementation and triglyceride lowering: systematic review",
                "authors": ["A B"],
                "journal": "J Lipids",
                "publication_year": 2023,
                "abstract": "Meta-analysis in adults showed omega-3 reduced triglycerides.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/1/",
            },
            {
                "pmid": "2",
                "title": "Eye movement replication study in adults",
                "authors": ["C D"],
                "journal": "J Vision",
                "publication_year": 2024,
                "abstract": "Assesses oculomotor endurance and visual processing in young adults.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/2/",
            },
        ]

    monkeypatch.setattr(PubMedClient, "search_articles", _mixed_search)
    with TestClient(app) as client:
        create = client.post("/claims", json={"user_text": "Does omega-3 supplementation reduce triglycerides in adults?"})
        claim_id = create.json()["claim_id"]
        adj = client.post(f"/claims/{claim_id}/adjudicate")
        adj_id = adj.json()["adjudication_id"]
        detail = client.get(f"/adjudications/{adj_id}").json()

    accepted_titles = [e["title"] for e in detail["evidence"]["accepted_evidence"]]
    rejected_titles = [e["title"] for e in detail["evidence"]["rejected_candidates"]]
    assert any("Omega-3" in t for t in accepted_titles)
    assert any("Eye movement" in t for t in rejected_titles)


def test_adjudication_survives_pubmed_provider_failures(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def _failing_search(self, query: str, retmax: int | None = None) -> list[dict]:  # noqa: ARG001
        raise ProviderError("PubMed request failed: timeout")

    monkeypatch.setattr(PubMedClient, "search_articles", _failing_search)

    with TestClient(app) as client:
        create = client.post("/claims", json={"user_text": "Does KRAS G12C predict response to KRAS inhibitors in NSCLC?"})
        claim_id = create.json()["claim_id"]

        adj = client.post(f"/claims/{claim_id}/adjudicate")
        assert adj.status_code == 200

        detail = client.get(f"/adjudications/{adj.json()['adjudication_id']}")
        assert detail.status_code == 200
        body = detail.json()
        assert body["evidence"]["accepted_evidence"] == []
        assert body["adjudication"]["best_supported_conclusion"]
