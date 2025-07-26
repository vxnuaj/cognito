import arxiv
from typing import List
from utils.shared_types import PaperMetadata
import requests
import os
import logging

class PaperFetcher:
    def search_arxiv(self, topic: str, max_results: int) -> List[PaperMetadata]:
        """
        Searches arXiv for papers matching the given topic.
        """
        logging.info(f"PaperFetcher: Searching arXiv for '{topic}' (max_results={max_results})...")
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending
        )

        papers = []
        try:
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
            logging.info(f"PaperFetcher: Found {len(papers)} papers for topic '{topic}'.")
        except Exception as e:
            logging.error(f"PaperFetcher: Error searching arXiv for '{topic}': {e}")
        return papers

    def download_paper(self, paper_metadata: PaperMetadata, download_dir: str) -> str:
        """
        Downloads the PDF of a paper to the specified directory.
        Returns the path to the downloaded PDF.
        """
        os.makedirs(download_dir, exist_ok=True)
        filename = f"{paper_metadata.arxiv_id}.pdf"
        filepath = os.path.join(download_dir, filename)

        if os.path.exists(filepath):
            logging.info(f"PaperFetcher: Paper already downloaded: {filepath}")
            return filepath

        logging.info(f"PaperFetcher: Downloading {paper_metadata.title} from {paper_metadata.pdf_url}...")
        try:
            response = requests.get(paper_metadata.pdf_url, stream=True)
            response.raise_for_status() # Raise an exception for HTTP errors

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.info(f"PaperFetcher: Downloaded to {filepath}")
            return filepath
        except requests.exceptions.RequestException as e:
            logging.error(f"PaperFetcher: Error downloading {paper_metadata.title}: {e}")
            return "" # Return empty string on error
