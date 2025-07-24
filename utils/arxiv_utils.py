import arxiv
from typing import List
from dataclasses import dataclass

@dataclass
class PaperMetadata:
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    pdf_url: str

def search_arxiv(topic: str, max_results: int) -> List[PaperMetadata]:
    """
    Searches arXiv for papers matching the given topic.
    """
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending
    )

    papers = []
    for result in search.results():
        papers.append(
            PaperMetadata(
                title=result.title,
                authors=[author.name for author in result.authors],
                abstract=result.summary,
                arxiv_id=result.entry_id.split('/')[-1],
                pdf_url=result.pdf_url
            )
        )
    return papers
