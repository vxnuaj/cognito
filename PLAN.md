# Technical Plan: Orgo-based Research Paper Summarization System

This document outlines the technical plan for building a research paper summarization system using Orgo AI Agents, as described in the project requirements. The system will automate the process of finding, processing, summarizing, and formatting research papers on a given topic.

## 1. Project Structure

```
orgo/
├── main.py
├── config.py
├── requirements.txt
├── PLAN.md
└── agents/
    ├── __init__.py
    ├── research_orchestrator.py  # Renamed from search_agent.py
    └── document_agent.py
└── utils/
    ├── __init__.py
    ├── arxiv_utils.py
    ├── pdf_processing_utils.py
    ├── shared_types.py
    ├── summarizer.py             # New utility for summarization
    ├── formatter.py              # New utility for formatting
    └── orgo_vm_scripts/          # These scripts are now largely illustrative
        ├── pdf_extractor.sh
        └── screenshot_tool.sh
```

## 2. Core Modules and Their Responsibilities

### `main.py`
-   **Purpose:** Entry point for the application.
-   **Responsibilities:**
    -   Parse command-line arguments (research topic, number of papers, number of VMs).
    -   **Enforce Constraint:** Ensure `num_papers` does not exceed `num_vms`.
    -   Initialize and orchestrate the workflow by calling the `ResearchOrchestrator`.
    -   Handle overall error reporting and progress display.

### `config.py`
-   **Purpose:** Centralized configuration for the application.
-   **Responsibilities:**
    -   Define constants such as default number of papers, default number of VMs. **Defaults adhere to `num_papers <= num_vms` constraint.**
    -   Store API keys (e.g., `ORGO_API_KEY`, `ANTHROPIC_API_KEY`) loaded from environment variables.
    -   Define paths for temporary files, output directories.

### `requirements.txt`
-   **Purpose:** Lists all Python dependencies.
-   **Dependencies:** `arxiv`, `requests`, `pypdf`, `orgo`, `anthropic`.

### `agents/` Directory

#### `agents/research_orchestrator.py` (AI Orchestrator Agent)
-   **Purpose:** The singular AI agent responsible for orchestrating the entire research paper summarization workflow.
-   **Input:** `research_topic` (str), `num_papers` (int), `num_vms` (int).
-   **Output:** Path to the generated Markdown summary file.
-   **Logic:**
    1.  Use the `arxiv` Python library (via `utils.arxiv_utils.search_arxiv`) to query arXiv for papers matching the `research_topic`.
    2.  Filter and select the top `num_papers` based on relevance.
    3.  **Orgo Integration:** For each selected paper, it will spawn an independent Orgo Computer-Use Agent (`DocumentAgent`) using `orgo.spawn_agent()`. It manages concurrency using `concurrent.futures.ThreadPoolExecutor` to respect the `num_vms` limit.
    4.  Collect `ExtractedContent` from each `DocumentAgent`'s output.
    5.  Pass the `ExtractedContent` and `PaperMetadata` to `utils.summarizer.Summarizer` to generate `Summary` objects.
    6.  Pass all `Summary` and `PaperMetadata` objects to `utils.formatter.Formatter` to compile the final Markdown report.
    7.  Save the Markdown report to the `OUTPUT_DIR`.

#### `agents/document_agent.py` (Computer-Use Agent)
-   **Purpose:** Operates within an Orgo VM, controlled by its internal LLM via `orgo.Computer`, to download PDFs, extract text, and capture screenshots.
-   **Input:** `PaperMetadata` object (specifically `pdf_url`, `arxiv_id`).
-   **Output:** `ExtractedContent` object (dataclass: `raw_text` (str), `image_data` (list of base64 encoded image strings)).
-   **Logic (executed within Orgo VM, controlled by `orgo.Computer`'s internal LLM):**
    1.  Instantiate `computer = Computer()`. This connects to the agent's dedicated VM.
    2.  **Download PDF:** Uses `computer.prompt()` to instruct the VM's LLM to download the PDF from `pdf_url` to a temporary location within the VM (e.g., `/tmp/`).
    3.  **Text Extraction:** Uses `computer.prompt()` to instruct the VM's LLM to open the downloaded PDF and extract its text content. The VM's LLM is prompted to return the raw text directly in its response.
    4.  **Screenshotting:** Uses `computer.prompt()` to instruct the VM's LLM to open the PDF. Then, it uses `computer.screenshot_base64()` to capture a base64-encoded screenshot of the VM's display (assuming the PDF is open and visible).
    5.  **Data Transfer:** Returns the `ExtractedContent` object, containing the extracted text and base64-encoded image data.
    6.  Ensures `computer.destroy()` is called in a `finally` block to release VM resources.

### `utils/` Directory

#### `utils/arxiv_utils.py`
-   **Purpose:** Encapsulate arXiv API interactions.
-   **Functions:**
    -   `search_arxiv(topic: str, max_results: int) -> List[PaperMetadata]`

#### `utils/pdf_processing_utils.py`
-   **Purpose:** (Now largely illustrative/fallback) Helper functions for PDF handling, primarily for local testing or if `orgo.Computer`'s LLM fails to perform the task.
-   **Functions:**
    -   `download_pdf(url: str, destination_path: str)`
    -   `extract_text_from_pdf(pdf_path: str) -> str`

#### `utils/shared_types.py`
-   **Purpose:** Defines shared data structures (dataclasses) used across different modules.
-   **Classes:** `ExtractedContent` (now with `image_data` as `List[str]` for base64), `Summary`.

#### `utils/summarizer.py`
-   **Purpose:** Provides a static utility class for generating structured summaries using an LLM.
-   **Class:** `Summarizer`
-   **Method:** `summarize_paper(extracted_content: ExtractedContent, paper_metadata: PaperMetadata) -> Summary`.
    -   Uses the `anthropic` SDK to interact with an LLM (e.g., Claude) to generate the summary based on the extracted text.
    -   Parses the LLM's response into the `Summary` object fields.

#### `utils/formatter.py`
-   **Purpose:** Provides a static utility class for compiling individual paper summaries into a single, comprehensive Markdown report.
-   **Class:** `Formatter`
-   **Method:** `format_markdown(summaries: List[Summary], papers_metadata: List[PaperMetadata]) -> str`.

#### `utils/orgo_vm_scripts/`
-   **Purpose:** (Now largely illustrative) Shell scripts that *could* be executed within an Orgo VM if direct command execution were preferred over LLM-driven interaction via `orgo.Computer`.
-   **`pdf_extractor.sh`:** Illustrates `pdftotext` usage.
-   **`screenshot_tool.sh`:** Illustrates `scrot` usage.

## 3. Workflow

1.  **Initialization (`main.py`):** User provides `research_topic`, `num_papers`, `num_vms`. Constraint `num_papers <= num_vms` is validated.
2.  **Paper Search (`ResearchOrchestrator`):**
    -   `ResearchOrchestrator` queries arXiv for `num_papers` related to `research_topic`.
    -   It collects `PaperMetadata` for each relevant paper.
3.  **Parallel Document Processing & Summarization (`ResearchOrchestrator` dispatches `DocumentAgent`s):**
    -   `ResearchOrchestrator` uses `ThreadPoolExecutor` to manage concurrent execution of `_process_single_paper` for each `PaperMetadata`, respecting `num_vms`.
    -   Inside `_process_single_paper`:
        -   An `orgo.Computer` instance is created within the `DocumentAgent`'s execution context, connecting to its dedicated VM.
        -   The `DocumentAgent` uses `computer.prompt()` to instruct the VM's internal LLM to download the PDF and extract text.
        -   It uses `computer.screenshot_base64()` to capture screenshots.
        -   The `ExtractedContent` is returned.
        -   The `ResearchOrchestrator` then calls `utils.summarizer.Summarizer.summarize_paper` with the `ExtractedContent` and `PaperMetadata` to get a `Summary`.
4.  **Result Collection (`ResearchOrchestrator`):**
    -   `ResearchOrchestrator` collects all `Summary` objects as they become available from the concurrent processing.
5.  **Final Formatting (`ResearchOrchestrator`):**
    -   `ResearchOrchestrator` invokes `utils.formatter.Formatter.format_markdown`.
    -   The `Formatter` compiles all `Summary` and `PaperMetadata` objects into a single, comprehensive Markdown report.
6.  **Output:** The final Markdown report is saved to a file.

## 4. Orgo Integration Details

-   **Computer-Use Agents:** The `DocumentAgent` is the primary use case for Orgo's Computer-Use Agents. It leverages `orgo.Computer` to interact with its VM via natural language prompts to the VM's internal LLM.
    -   **VM Setup:** The Orgo environment for these VMs must be configured on the Orgo platform to include necessary tools (e.g., a PDF viewer, `pdftotext` if `computer.prompt` uses it, `scrot` if `computer.screenshot_base64` relies on it internally, or a headless browser for rendering).
    -   **File Transfer/Data Extraction:** `computer.prompt()` is used to instruct the VM to download files and extract text, with the expectation that the VM's LLM will return the extracted text directly in its response. `computer.screenshot_base64()` directly retrieves image data.
-   **AI Orchestrator Agent:** `ResearchOrchestrator` acts as the top-level AI agent, using `orgo.spawn_agent()` to create and manage `DocumentAgent` instances. It orchestrates the entire workflow, including calling utility functions for summarization and formatting.
-   **Parallelization:** `ResearchOrchestrator` explicitly manages concurrency using `ThreadPoolExecutor` and `orgo.spawn_agent()` to ensure `num_vms` limits are respected.
-   **Error Handling & Monitoring:** Robust error handling is implemented for agent failures and LLM interactions. Orgo's platform-level monitoring would provide further insights.

## 5. Considerations and Potential Challenges

-   **Orgo VM Environment:** The exact capabilities and pre-installed tools within the Orgo VM are crucial. The `computer.prompt()`'s effectiveness depends on the VM's LLM's ability to interpret and execute commands in that environment.
-   **LLM Prompting for VM Control:** Crafting effective natural language prompts for `computer.prompt()` to reliably perform tasks like PDF download, text extraction, and screenshotting is critical and might require iteration.
-   **Parsing `computer.prompt()` Responses:** Extracting specific data (like raw text) from the `computer.prompt()`'s `messages` response requires careful parsing of the `block.type` and `block.content`.
-   **Screenshot Quality/Relevance:** Ensuring `computer.screenshot_base64()` captures relevant visual information (e.g., specific figures, not just the PDF viewer's UI) might be challenging and could require more advanced prompting or VM setup.
-   **LLM Token Limits:** When passing raw text to the `Summarizer`'s LLM, token limits must be managed (e.g., truncating text as done in `summarizer.py`).
-   **API Key Management:** Ensuring `ORGO_API_KEY` and `ANTHROPIC_API_KEY` are correctly set as environment variables.

This revised plan provides a detailed roadmap for implementing the research paper summarization system, leveraging the `orgo.Computer` capabilities for VM interaction and structuring the application around a central AI orchestrator and a dedicated Computer-Use Agent.