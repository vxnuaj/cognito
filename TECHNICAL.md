# Technical Implementation Plan

## 1. Overview

This document outlines the technical strategy for evolving the existing research paper summarization tool into the advanced, multi-agent system defined in `PLAN.md`. It details how current components will be refactored, what new components must be built, and how they will interact under the control of a central orchestrator.

---

## 2. Analysis of Current Implementation

The current system is a linear, parallelized pipeline:

-   **`main.py`**: Entry point, handles CLI arguments.
-   **`ResearchOrchestrator`**: Manages the flow using a `ThreadPoolExecutor`.
-   **`DocumentAgent`**: Uses an Orgo VM to download a PDF, extract raw text, and take a screenshot.
-   **`Summarizer`**: Uses the Anthropic API to generate a structured summary from the raw text.
-   **`Formatter`**: Compiles summaries into a single Markdown file.
-   **`arxiv_utils`**: Fetches paper metadata from arXiv.
-   **`shared_types`**: Defines `ExtractedContent` and `Summary` data classes.

This forms a solid foundation, but lacks the distinct analytical and critical steps of the new plan.

---

## 3. Proposed Technical Architecture

We will refactor the codebase into a modular, agent-based system. The `ResearchOrchestrator` will be upgraded from a simple parallel dispatcher to a sophisticated controller that executes a sequence of agents for each paper.

### 3.1. Data Flow and State Management

The orchestrator will manage a central state for each paper. The data will be enriched as it passes through the agent pipeline. We will define new shared data structures in `utils/shared_types.py`:

```python
# In utils/shared_types.py

from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class PaperMetadata:
    # (current implementation is good)
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    pdf_url: str

@dataclass
class StructuredContent:
    """Output of the Content Extractor Agent."""
    abstract: str
    introduction: str
    methodology: str
    results: str
    conclusion: str
    full_text: str
    figures: List[Dict[str, str]] = field(default_factory=list) # e.g., {"caption": "...", "base64_image": "..."}

@dataclass
class AnalysisResult:
    """Output of the Analyst Agent."""
    key_claims: List[str]
    metrics_and_results: Dict[str, str]
    methodology_summary: str
    mathematical_derivations: List[str]
    tldr: str
    eli5: str

@dataclass
class Critique:
    """Output of the Critic Agent."""
    corroborating_sources: List[Dict[str, str]] # e.g., {"title": "...", "url": "..."}
    conflicting_sources: List[Dict[str, str]]
    synthesis: str # A summary of the external validation findings

@dataclass
class PaperAnalysisState:
    """A single object to track the full analysis of one paper."""
    metadata: PaperMetadata
    structured_content: StructuredContent = None
    analysis: AnalysisResult = None
    critique: Critique = None
    final_report: str = None
```

### 3.2. Agent Implementation Details

#### **Agent 1: Paper Information Extraction**
-   **Existing Code**: `utils/arxiv_utils.py`.
-   **Plan**: Generalize this module.
    -   Rename `utils/arxiv_utils.py` to `utils/paper_fetcher.py`.
    -   The `search_arxiv` function will remain.
    -   Add new functions like `fetch_by_doi(doi: str)` and `fetch_by_url(url: str)`.
    -   This agent will be responsible for populating the `PaperMetadata` object.

#### **Agent 2: Content Classifier & Extractor**
-   **Existing Code**: `agents/document_agent.py`.
-   **Plan**: This agent needs a significant upgrade. Its sole responsibility will be to convert raw PDF/text into `StructuredContent`.
    -   The current `DocumentAgent`'s Orgo VM logic for downloading and extracting text will be the first step.
    -   A new, powerful LLM prompt will be added. This prompt will take the raw text and instruct the LLM to parse it into the fields of the `StructuredContent` dataclass (Abstract, Introduction, Methodology, etc.).
    -   The screenshot logic will be enhanced to capture figures and tables, potentially by prompting the VM to scroll and screenshot specific elements based on text cues.
    -   **File**: `agents/extractor_agent.py`.

#### **Agent 3: Analyst Agent**
-   **Existing Code**: `utils/summarizer.py`.
-   **Plan**: The `Summarizer`'s logic will be the seed for this new, more powerful agent. It will perform a deep, internal analysis.
    -   It will take `StructuredContent` as input.
    -   It will use a sophisticated LLM prompt to populate the `AnalysisResult` object, focusing on extracting claims, metrics, and summarizing the methodology.
    -   It may use a code interpreter tool for verifying mathematical claims if possible.
    -   **File**: `agents/analyst_agent.py`.

#### **Agent 4: Critic Agent**
-   **Existing Code**: None.
-   **Plan**: This agent will be built from scratch. It is the primary user of the CUA (web browsing) capability.
    -   It will take the `AnalysisResult` as input.
    -   It will formulate search queries based on the `key_claims` and `metrics_and_results`.
    -   It will use the `google_web_search` tool to find external sources.
    -   It will use further LLM calls to analyze the search results, identify corroborating or conflicting information, and populate the `Critique` object.
    -   **File**: `agents/critic_agent.py`.

#### **Agent 5: Synthesizer Agent**
-   **Existing Code**: `utils/formatter.py`.
-   **Plan**: This agent will replace the `Formatter`. It will be responsible for generating the final, human-readable report.
    -   It will take the `AnalysisResult` and `Critique` as input.
    -   It will use an LLM prompt to generate a comprehensive and nuanced summary, explicitly highlighting settled points versus uncertain ones, citing the sources found by the Critic.
    -   The output will be a well-structured Markdown string.
    -   **File**: `agents/synthesizer_agent.py`.

### 3.3. Orchestrator Refactoring

-   **Existing Code**: `agents/research_orchestrator.py`.
-   **Plan**: The `ResearchOrchestrator` will be rewritten to manage the new sequential, stateful workflow.
    -   The `ThreadPoolExecutor` will still be used, but each worker thread will execute the full agent pipeline for a single paper, not just one step.
    -   The main loop within a worker thread will look like this:
        ```python
        # Inside the orchestrator's worker function
        state = PaperAnalysisState(metadata=paper_metadata)

        extractor = ExtractorAgent()
        state.structured_content = extractor.run(state.metadata)

        analyst = AnalystAgent()
        state.analysis = analyst.run(state.structured_content)

        critic = CriticAgent()
        state.critique = critic.run(state.analysis)

        synthesizer = SynthesizerAgent()
        state.final_report = synthesizer.run(state.analysis, state.critique)

        return state
        ```
    -   The main `run` method will collect the final `PaperAnalysisState` objects and compile them into a single output file.

### 3.4. Proposed Directory Structure

```
/Users/juanvera/Documents/DEVELOPMENT/SINGULARITY/Projects/cognito/
├───.gitignore
├───config.py
├───main.py
├───PLAN.md
├───TECHNICAL.md  <-- This file
├───README.md
├───requirements.txt
├───agents/
│   ├───__init__.py
│   ├───extractor_agent.py       # New: Replaces DocumentAgent
│   ├───analyst_agent.py         # New: Replaces Summarizer
│   ├───critic_agent.py          # New
│   ├───synthesizer_agent.py     # New: Replaces Formatter
│   └───research_orchestrator.py # Refactored
├───output/
├───utils/
│   ├───__init__.py
│   ├───paper_fetcher.py         # New: Replaces arxiv_utils
│   └───shared_types.py          # Updated
└───venv/
```

---

## 4. Implementation Roadmap

This will be a phased implementation to ensure stability at each step.

-   **Phase 1: Core Refactoring.**
    1.  Update `shared_types.py` with the new data classes.
    2.  Rename `arxiv_utils.py` to `paper_fetcher.py`.
    3.  Convert the existing `DocumentAgent`, `Summarizer`, and `Formatter` into the new `ExtractorAgent`, `AnalystAgent`, and `SynthesizerAgent` classes. Initially, they can just wrap the old logic.
    4.  Rewrite the `ResearchOrchestrator` to implement the new sequential, state-passing logic.
    5.  *Goal*: The system should function end-to-end like the old one, but with the new architecture in place.

-   **Phase 2: Implement the Critic Agent.**
    1.  Create the `CriticAgent` class.
    2.  Implement the logic for generating search queries from the `AnalysisResult`.
    3.  Integrate the `google_web_search` tool.
    4.  Develop the LLM prompts to process search results and produce the `Critique` object.
    5.  Update the `SynthesizerAgent` to incorporate the `Critique` into the final report.

-   **Phase 3: Enhance Agent Intelligence.**
    1.  Iteratively improve the LLM prompts for all agents.
    2.  Refine the `ExtractorAgent` to better handle diverse PDF layouts.
    3.  Enhance the `AnalystAgent` to extract more nuanced information.
    4.  Improve the `CriticAgent`'s search and synthesis strategies.

-   **Phase 4: Final Polish.**
    1.  Add robust error handling and logging throughout the pipeline.
    2.  Improve the final Markdown report's formatting and presentation.
    3.  Add comprehensive documentation.
