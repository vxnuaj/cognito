import os
from typing import List
from concurrent.futures import ThreadPoolExecutor

from utils.arxiv_utils import search_arxiv, PaperMetadata
from utils.shared_types import ExtractedContent, Summary
from utils.summarizer import Summarizer
from utils.formatter import Formatter
from agents.document_agent import DocumentAgent

from config import DEFAULT_NUM_PAPERS, DEFAULT_NUM_VMS, TEMP_DIR, OUTPUT_DIR

class ResearchOrchestrator:
    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)
        self.summarizer = Summarizer()
        self.formatter = Formatter()

    def _process_single_paper(self, paper_metadata: PaperMetadata) -> Summary:
        """
        Processes a single paper: dispatches DocumentAgent and then summarizes.
        This method will be run in a separate thread by the ThreadPoolExecutor.
        """
        document_agent = DocumentAgent()
        extracted_content = document_agent.run(paper_metadata)
        summary = self.summarizer.summarize_paper(extracted_content, paper_metadata)
        return summary

    def run(self, research_topic: str, num_papers: int = DEFAULT_NUM_PAPERS, num_vms: int = DEFAULT_NUM_VMS) -> str:
        if num_papers > num_vms:
            print(f"Warning: Number of papers ({num_papers}) exceeds number of VMs ({num_vms}). Adjusting num_papers to {num_vms}.")
            num_papers = num_vms

        print(f"Searching arXiv for \"{research_topic}\" (top {num_papers} papers)...")
        papers_metadata = search_arxiv(research_topic, num_papers)

        if not papers_metadata:
            print("No papers found for the given topic.")
            return "No papers found."

        print(f"Found {len(papers_metadata)} papers. Dispatching Document Agents and Summarizers...")

        all_summaries: List[Summary] = []
        processed_papers_metadata: List[PaperMetadata] = []

        # Use ThreadPoolExecutor to manage concurrency for DocumentAgent runs
        with ThreadPoolExecutor(max_workers=num_vms) as executor:
            futures = [
                executor.submit(self._process_single_paper, paper_metadata)
                for paper_metadata in papers_metadata
            ]

            for i, future in enumerate(futures):
                paper_metadata = papers_metadata[i] # Get corresponding metadata
                try:
                    summary = future.result() # This blocks until the agent completes
                    all_summaries.append(summary)
                    processed_papers_metadata.append(paper_metadata)
                    print(f"Successfully processed and summarized: {paper_metadata.title}")
                except Exception as e:
                    print(f"Error processing paper {paper_metadata.title}: {e}")

        if not all_summaries:
            print("No summaries were generated.")
            return "No summaries were generated."

        print("\n--- Formatting results ---")
        final_markdown = self.formatter.format_markdown(all_summaries, processed_papers_metadata)

        output_filename = os.path.join(OUTPUT_DIR, f"{research_topic.replace(' ', '_')}_summaries.md")
        with open(output_filename, "w") as f:
            f.write(final_markdown)
        print(f"\nSummaries saved to {output_filename}")

        return output_filename