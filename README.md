# cognito

general purpose parallel agents

# usage ( for now )

### installation

```bash
git clone https://github.com/vxnuaj/cognito.git
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### note to every1

always git branch bro - never push to master unless we both discuss and agree to do so.

```bash
git checkout -b <branch_name>
git checkout <branch_name>
```

when pushing,

```bash
git add .
git commit -m "<commit_message>"
git push origin <branch_name> # always push to your branch bro
```


--------

# 🧠 Academic Insight Pipeline with Computer-Use Agents (Orgo.ai)

## Overview

This project builds an **automated academic insight pipeline** using Orgo.ai's computer-use agents. These agents can simulate human desktop behavior—opening browsers, typing, clicking, downloading files, reading PDFs, and synthesizing knowledge using AI models (e.g. Claude, GPT). The goal is to automate tasks like literature reviews, citation tracking, replication validation, and trend mapping.

---

## 🎯 Goals

- Automate literature discovery and synthesis
- Track academic trends and citation growth
- Replicate and benchmark research experiments
- Synthesize quantitative results across papers
- Map scientific debates and positions
- Deliver ongoing research insights to teams or labs

---

## 🔧 Tools & Platforms

- **Orgo.ai**: Virtual Ubuntu desktop automation (keyboard/mouse/screen access)
- **LLMs**: Claude, GPT for summarization, classification, and analysis
- **PDF Tools**: OCR + Table extractors (e.g. pdfplumber, tabula)
- **Notion / Google Sheets / Slack**: Output formats
- **GitHub / JupyterLab**: For reproducibility pipelines

---

## 🛠️ Pipeline Modules

### 1. Literature Review Agent
- Opens arXiv, Semantic Scholar, or Springer
- Types queries (e.g. "LLMs for drug discovery")
- Extracts metadata: titles, abstracts, links, PDFs
- Classifies relevance using LLMs
- Outputs Markdown summary or spreadsheet

---

### 2. Trend & Citation Tracker
- Logs into academic databases (Google Scholar, Scopus)
- Searches for target topics or papers
- Tracks citation growth over time
- Detects emergent keywords
- Plots results in Google Sheets or Matplotlib

---

### 3. Replication Validator
- Downloads GitHub repos from papers
- Launches Jupyter or VS Code
- Installs dependencies, runs scripts
- Logs outcomes (success/failure)
- Outputs reproducibility metrics per domain

---

### 4. Meta-Analysis Synthesizer
- Extracts quantitative results from papers
- Parses tables, charts, and figures using OCR + LLMs
- Aggregates metrics (accuracy, F1, AUC, etc.)
- Ranks and compares performance across studies
- Creates summary tables or visual dashboards

---

### 5. Academic Debate Mapper
- Constructs citation networks from paper links
- Extracts key claims and counterclaims
- Clusters papers by stance
- Annotates evidence, contradictions, and gaps
- Outputs structured map (graph or outline)

---

### 6. Daily Knowledge Feed
- Pulls recent papers via RSS or journal sites
- Generates TLDRs and summaries
- Clusters by topic (using embeddings or LLM)
- Sends daily digests to Slack, Notion, or email

---

## 🧩 Example Workflow: LLM Evaluation Monitor

1. `Agent A`: Searches arXiv daily for "LLM benchmarks"
2. `Agent B`: Parses papers to extract benchmark results (e.g., MMLU scores)
3. `Agent C`: Updates central leaderboard in Notion/Google Sheet
4. `Agent D`: Flags significant result deviations or new benchmarks

---

## ✨ Benefits

- Reduces researcher workload
- Makes scientific progress more accessible
- Enables real-time monitoring of developments
- Encourages reproducibility and accountability
- Bridges fragmented research knowledge into coherent insight

---

## 🔐 Considerations

- GUI flows can be brittle—requires robust exception handling
- Some academic sites block scraping or automated access
- PDF parsing quality varies—human fallback may be required
- Must track agent actions for transparency and auditability

---

## ✅ Next Steps

1. Define target research domain (e.g., bioinformatics, NLP)
2. Select primary data sources (arXiv, PubMed, Google Scholar)
3. Build MVP pipeline: discovery → extraction → summarization
4. Integrate outputs with Notion or Slack
5. Scale to include citation mapping or replication checks

---