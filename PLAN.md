# Research Paper Analysis Pipeline

## 1. High-Level Goal

To create a multi-agent system that automates the process of fetching, analyzing, and synthesizing research papers. The final output will be a rigorous analysis that highlights key findings, evaluates claims, and identifies areas of uncertainty, complete with citations and suggestions for future work.

## 2. System Architecture

The system will be coordinated by a central **Orchestrator**. The Orchestrator manages the workflow, passes data between specialized agents, and makes decisions about when to proceed, loop, or terminate the process.

The workflow follows these sequential steps:

**Paper -> Extraction -> Classification -> Analysis -> Criticism -> Synthesis -> Final Report**

---

## 3. Agent Definitions

### Agent 1: Paper Information Extraction

-   **Role**: Fetches the full content of a research paper given a URL, DOI, or title.
-   **Inputs**: Paper identifier (URL, DOI, arXiv ID, etc.).
-   **Outputs**: Raw, unstructured text content of the paper.
-   **CUA Requirement**: **CONDITIONAL**.
    -   **No CUA**: For sources with direct APIs (e.g., arXiv, PubMed).
    -   **CUA Required**: For sources behind paywalls, login pages, or complex web portals that require scraping.

### Agent 2: Content Classifier & Extractor

****-   **Role**: Processes the raw text to identify, label, and extract useful content. It filters out noise (e.g., headers, footers, irrelevant metadata) and structures the document.
-   **Inputs**: Raw text content from the Extraction Agent.
-   **Outputs**: A structured representation of the paper, with sections like "Abstract," "Introduction," "Methodology," "Results," and "Conclusion" clearly delineated. Key claims, figures, and tables are tagged.
-   **CUA Requirement**: **NO**. This is a pure text processing task.

### Agent 3: Analyst Agent

-   **Role**: Performs a deep analysis of the structured content. It identifies the core metrics, evaluates the methodology, and verifies mathematical derivations.
-   **Inputs**: Structured content from the Classifier Agent.
-   **Outputs**: A detailed internal analysis, including extracted metrics, comparisons presented in the paper, and validated mathematical claims.
-   **CUA Requirement**: **NO**. This agent performs internal reasoning and may use tools like a calculator or symbolic math solver, but does not need web access.

### Agent 4: Critic Agent

-   **Role**: Cross-examines the claims and findings from the Analyst Agent. It seeks external evidence to validate or challenge the paper's conclusions.
-   **Inputs**: The internal analysis from the Analyst Agent.
-   **Outputs**: A critical review containing corroborating evidence, counter-examples, or context from other sources.
-   **CUA Requirement**: **YES**. This agent's primary function is to search the web, find competing papers, check benchmark websites (e.g., "Papers with Code"), and gather external information to provide a robust critique.

### Agent 5: Synthesizer Agent

-   **Role**: Produces the final, comprehensive report. It integrates the findings from the Analyst and the counterpoints from the Critic into a balanced and well-structured document.
-   **Inputs**: The analyses from both the Analyst and Critic Agents.
-   **Outputs**: A final, rigorous review that:
    -   Summarizes the paper's contributions.
    -   Highlights what is settled vs. what is uncertain.
    -   Includes citations for all external sources.
    -   Suggests potential next steps for research.
-   **CUA Requirement**: **NO**. This is a text generation and formatting task. It may invoke local tools like LaTeX or BibTeX but does not require web browsing.

---

## 4. Orchestrator Logic

The **Orchestrator** is the central controller responsible for:

-   **State Management**: Keeping track of the outputs from each agent for a given task.
-   **Control Flow**: Executing the agents in the correct sequence.
-   **Iterative Refinement**: If the Critic Agent finds a significant flaw or new piece of information, the Orchestrator can loop back, sending the new data to the Analyst Agent for a revised analysis before proceeding to the Synthesizer.
-   **Error Handling**: Managing failures in any of the agents.
