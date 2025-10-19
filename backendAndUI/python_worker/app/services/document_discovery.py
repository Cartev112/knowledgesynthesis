"""
Document Discovery Service
Integrates with PubMed and ArXiv APIs to search for and retrieve relevant research papers.
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class PubMedSearcher:
    """Search and retrieve papers from PubMed."""
    
    BASE_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    BASE_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    BASE_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    
    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize PubMed searcher.
        
        Args:
            email: Email for NCBI (recommended for better rate limits)
            api_key: NCBI API key (optional, increases rate limits)
        """
        self.email = email or "knowledgesynthesis@example.com"
        self.api_key = api_key
    
    def search(self, query: str, max_results: int = 20) -> List[str]:
        """
        Search PubMed for papers matching the query.
        
        Args:
            query: Search query (e.g., "BRAF inhibitors melanoma")
            max_results: Maximum number of results to return
            
        Returns:
            List of PubMed IDs (PMIDs)
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "email": self.email,
            "sort": "relevance"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            response = requests.get(self.BASE_SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])
            
            logger.info(f"PubMed search for '{query}' returned {len(pmids)} results")
            return pmids
            
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []
    
    def get_paper_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch detailed metadata for papers.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of paper metadata dictionaries
        """
        if not pmids:
            return []
        
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "email": self.email
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            response = requests.get(self.BASE_FETCH_URL, params=params, timeout=15)
            response.raise_for_status()
            
            papers = self._parse_pubmed_xml(response.text)
            logger.info(f"Retrieved details for {len(papers)} papers")
            return papers
            
        except Exception as e:
            logger.error(f"Failed to fetch paper details: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict]:
        """Parse PubMed XML response into structured data."""
        papers = []
        
        try:
            root = ET.fromstring(xml_text)
            
            for article in root.findall(".//PubmedArticle"):
                try:
                    paper = self._extract_paper_info(article)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to parse PubMed XML: {e}")
        
        return papers
    
    def _extract_paper_info(self, article_elem) -> Optional[Dict]:
        """Extract paper information from XML element."""
        try:
            medline = article_elem.find(".//MedlineCitation")
            article = medline.find(".//Article")
            
            # PMID
            pmid_elem = medline.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None
            
            # Title
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "Untitled"
            
            # Abstract
            abstract_parts = []
            for abstract_text in article.findall(".//AbstractText"):
                if abstract_text.text:
                    label = abstract_text.get("Label", "")
                    text = abstract_text.text
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
            abstract = " ".join(abstract_parts) if abstract_parts else ""
            
            # Authors
            authors = []
            for author in article.findall(".//Author"):
                last_name = author.find("LastName")
                fore_name = author.find("ForeName")
                if last_name is not None and fore_name is not None:
                    authors.append(f"{fore_name.text} {last_name.text}")
                elif last_name is not None:
                    authors.append(last_name.text)
            
            # Journal
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else ""
            
            # Publication date
            pub_date = article.find(".//PubDate")
            year = pub_date.find("Year").text if pub_date is not None and pub_date.find("Year") is not None else ""
            
            # DOI
            doi = None
            for article_id in article_elem.findall(".//ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text
                    break
            
            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal,
                "year": year,
                "doi": doi,
                "source": "pubmed",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract paper info: {e}")
            return None


class ArXivSearcher:
    """Search and retrieve papers from ArXiv."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def search(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Search ArXiv for papers matching the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of paper metadata dictionaries
        """
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            papers = self._parse_arxiv_xml(response.text)
            logger.info(f"ArXiv search for '{query}' returned {len(papers)} results")
            return papers
            
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            return []
    
    def _parse_arxiv_xml(self, xml_text: str) -> List[Dict]:
        """Parse ArXiv XML response into structured data."""
        papers = []
        
        try:
            # ArXiv uses Atom namespace
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(xml_text)
            
            for entry in root.findall("atom:entry", ns):
                try:
                    paper = self._extract_arxiv_entry(entry, ns)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"Failed to parse ArXiv entry: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to parse ArXiv XML: {e}")
        
        return papers
    
    def _extract_arxiv_entry(self, entry, ns) -> Optional[Dict]:
        """Extract paper information from ArXiv entry."""
        try:
            # ID (extract ArXiv ID from URL)
            id_elem = entry.find("atom:id", ns)
            arxiv_id = id_elem.text.split("/")[-1] if id_elem is not None else None
            
            # Title
            title_elem = entry.find("atom:title", ns)
            title = title_elem.text.strip() if title_elem is not None else "Untitled"
            
            # Abstract
            summary_elem = entry.find("atom:summary", ns)
            abstract = summary_elem.text.strip() if summary_elem is not None else ""
            
            # Authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name_elem = author.find("atom:name", ns)
                if name_elem is not None:
                    authors.append(name_elem.text)
            
            # Published date
            published_elem = entry.find("atom:published", ns)
            published = published_elem.text[:4] if published_elem is not None else ""
            
            # Categories
            categories = [cat.get("term") for cat in entry.findall("atom:category", ns)]
            
            # PDF URL
            pdf_url = None
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href")
                    break
            
            return {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "year": published,
                "categories": categories,
                "source": "arxiv",
                "url": id_elem.text if id_elem is not None else None,
                "pdf_url": pdf_url
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract ArXiv entry: {e}")
            return None


class SemanticScholarSearcher:
    """Search and retrieve papers from Semantic Scholar."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RECOMMEND_URL = "https://api.semanticscholar.org/recommendations/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Semantic Scholar searcher.
        
        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key
        self.headers = {"x-api-key": api_key} if api_key else {}
    
    def search(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Search Semantic Scholar for papers.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of paper metadata dictionaries
        """
        params = {
            "query": query,
            "limit": max_results,
            "fields": "paperId,title,abstract,authors,year,venue,citationCount,influentialCitationCount,openAccessPdf,externalIds,fieldsOfStudy"
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            papers = response.json().get("data", [])
            result = [self._format_paper(p) for p in papers]
            
            logger.info(f"Semantic Scholar search for '{query}' returned {len(result)} results")
            return result
            
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return []
    
    def _format_paper(self, paper: Dict) -> Optional[Dict]:
        """Format Semantic Scholar paper to standard format."""
        try:
            authors = [a.get("name") for a in paper.get("authors", []) if a.get("name")]
            
            # Extract PDF URL
            pdf_url = None
            if paper.get("openAccessPdf"):
                pdf_url = paper["openAccessPdf"].get("url")
            
            # Build URL
            paper_id = paper.get("paperId")
            url = f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else None
            
            # Extract external IDs
            external_ids = paper.get("externalIds", {}) or {}
            
            return {
                "semantic_scholar_id": paper_id,
                "title": paper.get("title"),
                "abstract": paper.get("abstract"),
                "authors": authors,
                "year": str(paper.get("year", "")),
                "venue": paper.get("venue"),
                "citation_count": paper.get("citationCount", 0),
                "influential_citation_count": paper.get("influentialCitationCount", 0),
                "fields_of_study": paper.get("fieldsOfStudy", []),
                "source": "semantic_scholar",
                "url": url,
                "pdf_url": pdf_url,
                "doi": external_ids.get("DOI"),
                "pmid": external_ids.get("PubMed"),
                "arxiv_id": external_ids.get("ArXiv")
            }
            
        except Exception as e:
            logger.warning(f"Failed to format Semantic Scholar paper: {e}")
            return None


class DocumentDiscoveryService:
    """Unified service for discovering research papers across multiple sources."""
    
    def __init__(self, email: Optional[str] = None, pubmed_api_key: Optional[str] = None, semantic_scholar_api_key: Optional[str] = None):
        self.pubmed = PubMedSearcher(email=email, api_key=pubmed_api_key)
        self.arxiv = ArXivSearcher()
        self.semantic_scholar = SemanticScholarSearcher(api_key=semantic_scholar_api_key)
    
    def search_all(self, query: str, max_results_per_source: int = 10) -> Dict[str, List[Dict]]:
        """
        Search across all available sources.
        
        Args:
            query: Search query
            max_results_per_source: Max results from each source
            
        Returns:
            Dictionary with source names as keys and paper lists as values
        """
        results = {}
        
        # Search PubMed
        try:
            pmids = self.pubmed.search(query, max_results=max_results_per_source)
            pubmed_papers = self.pubmed.get_paper_details(pmids)
            results["pubmed"] = pubmed_papers
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            results["pubmed"] = []
        
        # Search ArXiv
        try:
            arxiv_papers = self.arxiv.search(query, max_results=max_results_per_source)
            results["arxiv"] = arxiv_papers
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            results["arxiv"] = []
        
        # Search Semantic Scholar
        try:
            semantic_scholar_papers = self.semantic_scholar.search(query, max_results=max_results_per_source)
            results["semantic_scholar"] = semantic_scholar_papers
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            results["semantic_scholar"] = []
        
        return results
    
    def search_combined(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Search all sources and return combined, deduplicated results.
        
        Args:
            query: Search query
            max_results: Total max results across all sources
            
        Returns:
            Combined list of papers
        """
        per_source = max_results // 3  # Split between three sources
        results = self.search_all(query, max_results_per_source=per_source)
        
        # Combine results
        combined = []
        combined.extend(results.get("pubmed", []))
        combined.extend(results.get("arxiv", []))
        combined.extend(results.get("semantic_scholar", []))
        
        # Deduplicate by title (simple approach)
        seen_titles = set()
        unique_papers = []
        for paper in combined:
            title_normalized = paper.get("title", "").lower().strip()
            if title_normalized and title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_papers.append(paper)
        
        return unique_papers[:max_results]
