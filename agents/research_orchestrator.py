import os
from typing import List
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime
from utils.cognito_thoughts import CognitoThoughts

from utils.paper_fetcher import PaperFetcher, PaperMetadata
from utils.shared_types import PaperAnalysisState, StructuredContent, AnalysisResult, Critique
from agents.extractor_agent import ExtractorAgent
from agents.analyst_agent import AnalystAgent
from agents.critic_agent import CriticAgent
from agents.synthesizer_agent import SynthesizerAgent
from agents.prompts import CONSOLIDATION_SYSTEM_PROMPT, CONSOLIDATION_USER_PROMPT

from config import DEFAULT_NUM_PAPERS, DEFAULT_NUM_VMS, TEMP_DIR, OUTPUT_DIR, ANTHROPIC_API_KEY, LLM_MODEL_NAME

class ResearchOrchestrator:
    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)
        self.paper_fetcher = PaperFetcher()
        self.extractor_agent = ExtractorAgent()
        self.analyst_personas = [
            "The Skeptic",
            "The Proponent",
            "The Pragmatist",
            "The Formalist",
            "The Strategist"
        ]
        self.analysts = [AnalystAgent(persona=p) for p in self.analyst_personas]
        self.critic_agent = CriticAgent()
        self.synthesizer_agent = SynthesizerAgent()
        
        # Initialize thoughts logger
        self.thoughts = CognitoThoughts(agent_name="Orchestrator")

    def _process_single_paper(self, paper_metadata: PaperMetadata, paper_index: int, total_papers: int) -> PaperAnalysisState:
        """
        Processes a single paper through the entire agent pipeline.
        """
        # Create a state object to track the analysis throughout the pipeline
        state = PaperAnalysisState(metadata=paper_metadata)
        start_time = datetime.now()
        
        print(f"\n[{paper_index}/{total_papers}] Processing: {paper_metadata.title}")
        print("-" * 80)
        
        self.thoughts.step("Paper Analysis", f"Starting analysis for: {paper_metadata.title[:50]}...")
        self.thoughts.analyze(f"ArXiv ID: {paper_metadata.arxiv_id}")
        
        # 1. Extract content
        try:
            print(f"[{paper_index}/{total_papers}] Step 1/5: Extracting content...")
            self.thoughts.step("Content Extraction", "Using ExtractorAgent")
            state.structured_content = self.extractor_agent.run(paper_metadata)
            if not state.structured_content:
                self.thoughts.error("Extraction failed", f"No content extracted for {paper_metadata.arxiv_id}")
                raise ValueError("Failed to extract content")
            self.thoughts.success("Content extracted successfully")
            print(f"[{paper_index}/{total_papers}] ✓ Content extracted successfully")
        except Exception as e:
            print(f"[{paper_index}/{total_papers}] ✗ Extraction failed: {e}")
            logging.error(f"Extraction failed for paper {paper_metadata.title}: {e}")
            self.thoughts.error(f"Extraction failed: {str(e)}", f"Paper: {paper_metadata.title}")
            return state

        # 2. Run Analyst Ensemble
        print(f"[{paper_index}/{total_papers}] Step 2/5: Running analyst ensemble ({len(self.analyst_personas)} personas)...")
        self.thoughts.step("Analyst Ensemble", f"Running {len(self.analysts)} different expert analyses")
        
        def analyze_with_persona(analyst):
            self.thoughts.analyze(f"Running analysis with: {analyst.persona}")
            return analyst.run(state.structured_content)
        
        with ThreadPoolExecutor(max_workers=len(self.analysts)) as executor:
            individual_analyses = list(executor.map(analyze_with_persona, self.analysts))
        
        self.thoughts.success(f"Completed {len(individual_analyses)} analyst perspectives")
        
        # 3. Consolidate Analyses
        print(f"[{paper_index}/{total_papers}] Step 3/5: Consolidating analyses...")
        self.thoughts.step("Analysis Consolidation", "Merging multiple perspectives")
        try:
            state.analysis = self.consolidate_analyses(individual_analyses)
            print(f"[{paper_index}/{total_papers}] ✓ Analyses consolidated")
            self.thoughts.success("Analyses consolidated")
        except Exception as e:
            print(f"[{paper_index}/{total_papers}] ✗ Consolidation failed: {e}")
            logging.error(f"Consolidation failed: {e}")
            self.thoughts.error(f"Consolidation failed: {str(e)}", f"Paper: {paper_metadata.title}")
            return state

        # 4. Run Critic
        print(f"[{paper_index}/{total_papers}] Step 4/5: Running external validation...")
        self.thoughts.step("External Validation", "Using CriticAgent for fact-checking")
        try:
            state.critique = self.critic_agent.run(state.analysis, state.metadata)
            print(f"[{paper_index}/{total_papers}] ✓ External validation complete")
            self.thoughts.success("External validation completed")
        except Exception as e:
            print(f"[{paper_index}/{total_papers}] ✗ External validation failed: {e}")
            logging.error(f"Critic failed: {e}")
            self.thoughts.error(f"External validation failed: {str(e)}", f"Paper: {paper_metadata.title}")
            # Continue without critique

        # 5. Synthesize Final Report
        print(f"[{paper_index}/{total_papers}] Step 5/5: Synthesizing final report...")
        self.thoughts.step("Report Generation", "Creating final synthesis")
        try:
            state.final_report = self.synthesizer_agent.run(state.analysis, state.critique)
            print(f"[{paper_index}/{total_papers}] ✓ Report synthesized")
            self.thoughts.success("Report synthesized")
        except Exception as e:
            print(f"[{paper_index}/{total_papers}] ✗ Synthesis failed: {e}")
            logging.error(f"Synthesizer failed: {e}")
            self.thoughts.error(f"Synthesis failed: {str(e)}", f"Paper: {paper_metadata.title}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"[{paper_index}/{total_papers}] Completed in {elapsed:.1f} seconds")
        self.thoughts.success(f"Paper analysis complete: {paper_metadata.title[:50]}...")
        
        return state

    def consolidate_analyses(self, individual_analyses: List[AnalysisResult]) -> AnalysisResult:
        print("Orchestrator: Consolidating analyses from multiple Analyst Agents...")
        self.thoughts.step("LLM Consolidation", f"Synthesizing {len(individual_analyses)} analyses")
        
        # Format analyses for prompt
        analyses_text = "\n\n---\n\n".join([
            f"Analysis {i+1}:\n{json.dumps(analysis.model_dump(), indent=2)}"
            for i, analysis in enumerate(individual_analyses)
        ])
        
        # Prepare prompt
        user_prompt = CONSOLIDATION_USER_PROMPT.format(
            count=len(individual_analyses),
            analyses=analyses_text
        )
        
        try:
            self.thoughts.decide("Use LLM consolidation", "Better synthesis than simple merging")
            # Call LLM for consolidation
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=LLM_MODEL_NAME,
                max_tokens=4096,
                system=CONSOLIDATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            result_text = response.content[0].text
            # Parse with Pydantic
            consolidated = AnalysisResult.model_validate_json(result_text)
            logging.info("Successfully consolidated analyses using LLM")
            self.thoughts.success("LLM consolidation successful")
            self.thoughts.insight(f"Consolidated to {len(consolidated.key_claims)} key claims")
            return consolidated
            
        except Exception as e:
            logging.error(f"LLM consolidation failed: {e}, falling back to simple merging")
            self.thoughts.error(f"LLM consolidation failed: {str(e)}", "Using fallback strategy")
            
            # Fall back to original simple consolidation logic
            consolidated_key_claims = []
            consolidated_metrics_and_results = {}
            consolidated_methodology_summary = ""
            consolidated_mathematical_derivations = []
            consolidated_tldr = ""
            consolidated_eli5 = ""

            for analysis in individual_analyses:
                consolidated_key_claims.extend(analysis.key_claims)
                consolidated_metrics_and_results.update(analysis.metrics_and_results)
                if not consolidated_methodology_summary and analysis.methodology_summary:
                    consolidated_methodology_summary = analysis.methodology_summary
                consolidated_mathematical_derivations.extend(analysis.mathematical_derivations)
                if not consolidated_tldr and analysis.tldr:
                    consolidated_tldr = analysis.tldr
                if not consolidated_eli5 and analysis.eli5:
                    consolidated_eli5 = analysis.eli5

            # Remove duplicates from lists
            consolidated_key_claims = list(dict.fromkeys(consolidated_key_claims))
            consolidated_mathematical_derivations = list(dict.fromkeys(consolidated_mathematical_derivations))

            return AnalysisResult(
                key_claims=consolidated_key_claims,
                metrics_and_results=consolidated_metrics_and_results,
                methodology_summary=consolidated_methodology_summary,
                mathematical_derivations=consolidated_mathematical_derivations,
                tldr=consolidated_tldr,
                eli5=consolidated_eli5
            )

    def run(self, research_topic: str, num_papers: int = DEFAULT_NUM_PAPERS, num_vms: int = DEFAULT_NUM_VMS) -> str:
        if num_papers > num_vms:
            print(f"Warning: Number of papers ({num_papers}) exceeds number of VMs ({num_vms}). Adjusting num_papers to {num_vms}.")
            num_papers = num_vms

        print(f"\n🔍 Searching arXiv for \"{research_topic}\" (top {num_papers} papers)...")
        papers_metadata = self.paper_fetcher.search_arxiv(research_topic, num_papers)

        if not papers_metadata:
            print("No papers found for the given topic.")
            return "No papers found."

        print(f"✓ Found {len(papers_metadata)} papers. Dispatching agents...")
        print("=" * 80)

        all_analysis_states: List[PaperAnalysisState] = []
        start_time = datetime.now()

        # Use ThreadPoolExecutor to manage concurrency for paper processing
        with ThreadPoolExecutor(max_workers=num_vms) as executor:
            futures = [
                executor.submit(self._process_single_paper, paper_metadata, i+1, len(papers_metadata))
                for i, paper_metadata in enumerate(papers_metadata)
            ]

            for i, future in enumerate(futures):
                paper_metadata = papers_metadata[i] # Get corresponding metadata
                try:
                    analysis_state = future.result() # This blocks until the agent completes
                    all_analysis_states.append(analysis_state)
                    print(f"\n✓ Successfully processed paper {i+1}/{len(papers_metadata)}: {paper_metadata.title}")
                except Exception as e:
                    print(f"\n✗ Error processing paper {i+1}/{len(papers_metadata)} {paper_metadata.title}: {e}")

        if not all_analysis_states:
            print("No analyses were generated.")
            return "No analyses were generated."

        print("\n" + "=" * 80)
        print("📝 Formatting final results...")
        # The final report is now generated by the SynthesizerAgent within _process_single_paper
        # We'll just concatenate them here for now, or decide on a different final output strategy
        final_markdown_output = "# Consolidated Research Report\n\n"
        for state in all_analysis_states:
            if state.final_report:
                final_markdown_output += f"## Paper: {state.metadata.title}\n\n"
                final_markdown_output += state.final_report
                final_markdown_output += "\n\n---\n\n"

        output_filename = os.path.join(OUTPUT_DIR, f"{research_topic.replace(' ', '_')}_report.md")
        with open(output_filename, "w") as f:
            f.write(final_markdown_output)
        print(f"\nReport saved to: {output_filename}")
        
        total_elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✓ All papers processed in {total_elapsed:.1f} seconds")
        print(f"📄 Output saved to: {output_filename}")
        
        return output_filename