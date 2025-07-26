"""Extractor Agent - Extracts structured content from research papers."""
import os
import json
import logging
import tarfile
import re
from typing import Tuple, List, Dict

import fitz  # PyMuPDF

from agents.base_agent import BaseAgent
from agents.prompts import EXTRACTOR_SYSTEM_PROMPT, EXTRACTOR_USER_PROMPT
from utils.shared_types import PaperMetadata, StructuredContent
from utils.paper_fetcher import PaperFetcher
from config import PDF_DIR


class ExtractorAgent(BaseAgent):
    """Agent that extracts structured content from research papers."""
    
    def __init__(self):
        """Initialize the extractor agent."""
        super().__init__("ExtractorAgent")
        self.paper_fetcher = PaperFetcher(PDF_DIR)
        
    def extract_from_latex_source(self, source_path: str) -> Tuple[str, List[Dict[str, str]]]:
        """Extract text and figures from LaTeX source tar.gz file."""
        self.logger.info(f"Extracting from LaTeX source: {source_path}")
        self.thoughts.step("LaTeX Extraction", f"Processing {source_path}")
        
        full_text = ""
        figures = []
        
        try:
            with tarfile.open(source_path, 'r:gz') as tar:
                tex_files_count = 0
                for member in tar.getmembers():
                    if member.name.endswith('.tex'):
                        tex_files_count += 1
                        tex_file = tar.extractfile(member)
                        if tex_file:
                            content = tex_file.read().decode('utf-8', errors='ignore')
                            
                            content = re.sub(r'%.*$', '', content, flags=re.MULTILINE)
                            
                            caption_pattern = r'\\caption\{([^}]+)\}'
                            captions_found = 0
                            for match in re.finditer(caption_pattern, content):
                                captions_found += 1
                                figures.append({
                                    'caption': match.group(1).strip(),
                                    'description': f"Figure from {member.name}"
                                })
                            
                            if captions_found > 0:
                                self.thoughts.analyze(f"Found {captions_found} figure captions in {member.name}")
                            
                            text_content = re.sub(r'\\[a-zA-Z]+\*?\s*(?:\[[^\]]*\])?\s*(?:\{[^}]*\})?', ' ', content)
                            text_content = re.sub(r'[{}]', ' ', text_content)
                            text_content = re.sub(r'\s+', ' ', text_content)
                            
                            full_text += text_content + "\n"
            
            self.thoughts.insight(f"Processed {tex_files_count} .tex files")
            self.logger.info(f"Extracted {len(full_text)} chars and {len(figures)} figures from LaTeX")
            self.thoughts.success(f"LaTeX extraction complete: {len(full_text)} chars, {len(figures)} figures")
            return full_text.strip(), figures
            
        except Exception as e:
            self.logger.error(f"Error extracting LaTeX source: {e}")
            self.thoughts.error(f"LaTeX extraction failed: {str(e)}", "Will fall back to PDF extraction")
            return "", []
    
    def extract_from_pdf(self, pdf_path: str) -> Tuple[str, List[Dict[str, str]]]:
        """Extract text and figures from PDF file."""
        self.logger.info(f"Extracting from PDF: {pdf_path}")
        self.thoughts.step("PDF Extraction", f"Processing {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            figures = []
            
            self.thoughts.progress(0, doc.page_count, "Extracting PDF pages")
            
            for page_num, page in enumerate(doc):
                full_text += page.get_text() + "\n"
                
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    figures.append({
                        "caption": f"Figure from page {page_num + 1}",
                        "description": f"Image {img_index + 1} on page {page_num + 1}"
                    })
                
                if (page_num + 1) % 5 == 0:
                    self.thoughts.progress(page_num + 1, doc.page_count, "Extracting PDF pages")
            
            doc.close()
            self.logger.info(f"Extracted {len(full_text)} chars and {len(figures)} figures from PDF")
            self.thoughts.success(f"PDF extraction complete: {len(full_text)} chars, {len(figures)} figures")
            return full_text, figures
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF: {e}")
            self.thoughts.error(f"PDF extraction failed: {str(e)}")
            return "", []
    
    def run(self, metadata: PaperMetadata) -> StructuredContent:
        """Extract structured content from a research paper."""
        self.logger.info(f"Processing paper: {metadata.title}")
        self.thoughts.step("Starting Extraction", f"Paper: {metadata.title[:50]}...")
        self.thoughts.analyze(f"ArXiv ID: {metadata.arxiv_id}")
        
        # Try LaTeX source first
        self.thoughts.decide("Try LaTeX source first", "LaTeX preserves more structure than PDF")
        source_path = self.paper_fetcher.download_paper_source(metadata.arxiv_id)
        
        if source_path and os.path.exists(source_path):
            full_text, figures = self.extract_from_latex_source(source_path)
            if full_text:
                self.logger.info("Successfully extracted from LaTeX source")
                self.thoughts.success("LaTeX extraction successful")
            else:
                self.logger.info("LaTeX extraction failed, falling back to PDF")
                self.thoughts.decide("Fall back to PDF", "LaTeX extraction returned no content")
                full_text = ""
                figures = []
        else:
            self.thoughts.analyze("No LaTeX source available")
        
        # Fall back to PDF if needed
        if not full_text:
            self.thoughts.step("PDF Fallback", "Downloading and extracting from PDF")
            pdf_path = self.paper_fetcher.download_paper(metadata.arxiv_id, metadata.pdf_url)
            if not pdf_path:
                self.thoughts.error("Failed to download paper", f"ArXiv ID: {metadata.arxiv_id}")
                raise ValueError(f"Failed to download paper: {metadata.arxiv_id}")
            
            full_text, figures = self.extract_from_pdf(pdf_path)
            
            if not full_text:
                self.thoughts.error("No content extracted", "Both LaTeX and PDF extraction failed")
                raise ValueError("Failed to extract any content from paper")
      
        '''
        TODO - rather than taking only a portion of the text, we could chunk the text into smaller sections and extract each section separately. 
        '''
        self.thoughts.question("Should we chunk text for better extraction?")
        
        # Use LLM to structure the content
        self.thoughts.step("Content Structuring", "Using LLM to organize extracted text")
        text_length = len(full_text)
        truncated_length = min(50000, text_length)
        if text_length > truncated_length:
            self.thoughts.analyze(f"Truncating text from {text_length} to {truncated_length} chars")
            
        user_prompt = EXTRACTOR_USER_PROMPT.format(content=full_text[:50000])  # Limit to prevent token overflow
        
        try:
            message = self._call_llm(EXTRACTOR_SYSTEM_PROMPT, user_prompt)
            response_text = message.content[0].text
            
            self.thoughts.step("Parsing LLM Response", "Converting to structured format")
            result = StructuredContent.model_validate_json(response_text)
            
            result.figures = figures
            
            self.logger.info("Successfully structured content")
            self.thoughts.success("Content extraction complete")
            self.thoughts.insight(f"Extracted {len(result.abstract)} char abstract, {len(result.figures)} figures")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to structure content: {e}")
            self.thoughts.error(f"LLM structuring failed: {str(e)}", "Returning basic structure")
            return StructuredContent(
                abstract=metadata.abstract,
                introduction="Content extraction failed",
                methodology="Content extraction failed",
                results="Content extraction failed", 
                conclusion="Content extraction failed",
                full_text=full_text[:10000],  # Truncate if too long
                figures=figures
            )