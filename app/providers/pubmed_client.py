import asyncio
import logging
import re
from xml.etree import ElementTree

import httpx

from app.core.config import settings
from app.core.exceptions import ProviderError

logger = logging.getLogger(__name__)


class PubMedClient:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self) -> None:
        self.max_results = settings.pubmed_max_results

    async def _request_with_retry(self, client: httpx.AsyncClient, path: str, params: dict, retries: int = 2) -> httpx.Response:
        for attempt in range(retries + 1):
            try:
                resp = await client.get(f"{self.BASE_URL}/{path}", params=params)
                resp.raise_for_status()
                return resp
            except Exception as exc:  # noqa: BLE001
                if attempt == retries:
                    raise ProviderError(f"PubMed request failed: {exc}") from exc
                await asyncio.sleep(0.3 * (attempt + 1))
        raise ProviderError("PubMed request failed")

    async def search_articles(self, query: str, retmax: int | None = None) -> list[dict]:
        retmax = retmax or self.max_results
        if query.upper().startswith("MOCK:"):
            return [
                {
                    "pmid": "12345678",
                    "title": "Mocked evidence on pathway interactions",
                    "authors": ["Doe J", "Roe A"],
                    "journal": "Mock Journal",
                    "publication_year": 2024,
                    "abstract": "This mocked abstract provides a deterministic branch-level finding for tests.",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                }
            ]

        params_common = {"tool": settings.pubmed_tool, "email": settings.pubmed_email}
        if settings.pubmed_api_key:
            params_common["api_key"] = settings.pubmed_api_key

        async with httpx.AsyncClient(timeout=15.0) as client:
            search_resp = await self._request_with_retry(
                client,
                "esearch.fcgi",
                {
                    **params_common,
                    "db": "pubmed",
                    "retmode": "json",
                    "term": query,
                    "retmax": retmax,
                },
            )
            idlist = search_resp.json().get("esearchresult", {}).get("idlist", [])
            pmids = list(dict.fromkeys(idlist))
            if not pmids:
                return []

            fetch_resp = await self._request_with_retry(
                client,
                "efetch.fcgi",
                {
                    **params_common,
                    "db": "pubmed",
                    "retmode": "xml",
                    "rettype": "abstract",
                    "id": ",".join(pmids),
                },
            )

        try:
            return self._parse_efetch_xml(fetch_resp.text)
        except ElementTree.ParseError as exc:
            raise ProviderError(f"PubMed XML parse failed: {exc}") from exc

    def _parse_efetch_xml(self, xml_text: str) -> list[dict]:
        root = ElementTree.fromstring(xml_text)
        articles: list[dict] = []
        for art in root.findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID")
            title = self._normalize_whitespace(self._node_text(art.find(".//ArticleTitle")))
            journal = art.findtext(".//Journal/Title") or ""
            year = self._extract_year(art)
            authors = []
            for a in art.findall(".//Author"):
                collective = self._normalize_whitespace(a.findtext("CollectiveName") or "")
                if collective:
                    authors.append(collective)
                    continue
                lastname = a.findtext("LastName") or ""
                initials = a.findtext("Initials") or ""
                val = f"{lastname} {initials}".strip()
                if val:
                    authors.append(val)
            abstract_text = self._normalize_whitespace(" ".join(self._node_text(x) for x in art.findall(".//Abstract/AbstractText")))
            articles.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "authors": authors,
                    "journal": journal,
                    "publication_year": year,
                    "abstract": abstract_text,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                }
            )
        logger.info("PubMed parsed %s articles", len(articles))
        return articles

    @staticmethod
    def _node_text(node: ElementTree.Element | None) -> str:
        if node is None:
            return ""
        return "".join(node.itertext())

    @staticmethod
    def _normalize_whitespace(value: str) -> str:
        return " ".join(value.split())

    @staticmethod
    def _extract_year(article_node: ElementTree.Element) -> int | None:
        candidate_paths = [
            ".//JournalIssue/PubDate/Year",
            ".//ArticleDate/Year",
            ".//PubDate/Year",
            ".//DateCompleted/Year",
            ".//DateRevised/Year",
            ".//MedlineDate",
        ]
        for path in candidate_paths:
            value = article_node.findtext(path)
            if not value:
                continue
            year_match = re.search(r"\b(19|20)\d{2}\b", value)
            if year_match:
                return int(year_match.group(0))
        return None
