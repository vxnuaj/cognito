from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class PaperMetadata(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    pdf_url: str


class StructuredContent(BaseModel):
    """Output of the Content Extractor Agent."""
    abstract: str
    introduction: str
    methodology: str
    results: str
    conclusion: str
    full_text: str
    figures: List[Dict[str, str]] = Field(default_factory=list)  # e.g., {"caption": "...", "base64_image": "..."}


class AnalysisResult(BaseModel):
    """Output of the Analyst Agent."""
    key_claims: List[str]
    metrics_and_results: Dict[str, str]
    methodology_summary: str
    mathematical_derivations: List[str]
    tldr: str
    eli5: str


class Critique(BaseModel):
    """Output of the Critic Agent."""
    corroborating_sources: List[Dict[str, str]]  # e.g., {"title": "...", "url": "..."}
    conflicting_sources: List[Dict[str, str]]
    synthesis: str  # A summary of the external validation findings


class PaperAnalysisState(BaseModel):
    """A single object to track the full analysis of one paper."""
    metadata: PaperMetadata
    structured_content: Optional[StructuredContent] = None
    analysis: Optional[AnalysisResult] = None
    critique: Optional[Critique] = None
    final_report: Optional[str] = None