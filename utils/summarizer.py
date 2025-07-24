from typing import List
from utils.shared_types import ExtractedContent, Summary
from utils.arxiv_utils import PaperMetadata
import anthropic
import os
from config import ANTHROPIC_API_KEY, LLM_MODEL_NAME

class Summarizer:
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def summarize_paper(self, extracted_content: ExtractedContent, paper_metadata: PaperMetadata) -> Summary:
        print(f"Summarizer: Summarizing {paper_metadata.title} using LLM...")

        raw_text = extracted_content.raw_text
        # For now, we'll only use text content for summarization.
        # Multimodal input with images would require more advanced LLM integration.

        prompt = f"""
            You are an expert research paper summarizer. 
            Your task is to provide a structured summary of the following research paper. 
            Focus on conciseness and accuracy.
            
            Paper Title: {paper_metadata.title}
            Authors: {', '.join(paper_metadata.authors)}
            Abstract: {paper_metadata.abstract}

            Full Paper Text (partial, for context):
            ---
            {raw_text[:4000]} # Limit text to avoid exceeding token limits
            ---

            Provide the summary in the following structured format:
            TL;DR:
            Key Contributions:
            Novelty:
            Limitations and Criticisms:
            Explain Like I'm 5:

            Ensure each section is clearly delineated.
            """

        try:
            message = self.client.messages.create(
                model=LLM_MODEL_NAME,
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            summary_text = message.content[0].text

            # Parse the structured summary
            tldr = self._extract_section(summary_text, "TL;DR:")
            key_contributions = self._extract_section(summary_text, "Key Contributions:")
            novelty = self._extract_section(summary_text, "Novelty:")
            limitations_criticisms = self._extract_section(summary_text, "Limitations and Criticisms:")
            explain_like_im_5 = self._extract_section(summary_text, "Explain Like I'm 5:")

            return Summary(
                tldr=tldr,
                key_contributions=key_contributions,
                novelty=novelty,
                limitations_criticisms=limitations_criticisms,
                explain_like_im_5=explain_like_im_5
            )
        except Exception as e:
            print(f"Error during summarization for {paper_metadata.title}: {e}")
            # Return a dummy summary in case of error
            return Summary(
                tldr=f"Error summarizing {paper_metadata.title}",
                key_contributions="",
                novelty="",
                limitations_criticisms="",
                explain_like_im_5=""
            )

    def _extract_section(self, text: str, section_header: str) -> str:
        start_index = text.find(section_header)
        if start_index == -1:
            return ""
        start_index += len(section_header)
        
        # Find the start of the next section header or end of text
        next_headers = [
            "TL;DR:",
            "Key Contributions:",
            "Novelty:",
            "Limitations and Criticisms:",
            "Explain Like I'm 5:",
        ]
        
        end_index = len(text)
        for header in next_headers:
            if header != section_header:
                current_end = text.find(header, start_index)
                if current_end != -1 and current_end < end_index:
                    end_index = current_end
        
        return text[start_index:end_index].strip()
