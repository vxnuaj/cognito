"""Synthesizer Agent - Creates comprehensive final reports."""
import logging

from agents.base_agent import BaseAgent
from agents.prompts import SYNTHESIZER_SYSTEM_PROMPT, SYNTHESIZER_USER_PROMPT
from utils.shared_types import AnalysisResult, Critique


class SynthesizerAgent(BaseAgent):
    """Agent that synthesizes analysis and critique into final reports."""
    
    def __init__(self):
        """Initialize the synthesizer agent."""
        super().__init__("SynthesizerAgent")
        
    def run(self, analysis: AnalysisResult, critique: Critique = None) -> str:
        """
        Synthesize analysis and critique into a comprehensive final report.
        
        Args:
            analysis: The analysis results to synthesize
            critique: Optional external validation results
            
        Returns:
            Final report as formatted markdown string
        """
        self.logger.info("Synthesizing final report")
        self.thoughts.step("Report Synthesis", "Creating comprehensive research summary")
        
        # Format analysis for prompt
        self.thoughts.analyze(f"Processing {len(analysis.key_claims)} key claims")
        analysis_text = f"""
Key Claims:
{chr(10).join(f"- {claim}" for claim in analysis.key_claims)}

Metrics and Results:
{chr(10).join(f"- {k}: {v}" for k, v in analysis.metrics_and_results.items())}

Methodology Summary:
{analysis.methodology_summary}

Mathematical Derivations:
{chr(10).join(f"- {deriv}" for deriv in analysis.mathematical_derivations) if analysis.mathematical_derivations else "None"}

TL;DR: {analysis.tldr}

ELI5: {analysis.eli5}
"""
        
        # Format critique if available
        critique_text = "No external validation performed."
        if critique:
            self.thoughts.step("External Validation", "Incorporating critique findings")
            self.thoughts.analyze(f"Found {len(critique.corroborating_sources)} corroborating sources, "
                               f"{len(critique.conflicting_sources)} conflicting sources")
            critique_text = f"""
Corroborating Sources ({len(critique.corroborating_sources)}):
{chr(10).join(f"- {s['title']} ({s.get('url', 'N/A')})" for s in critique.corroborating_sources)}

Conflicting Sources ({len(critique.conflicting_sources)}):
{chr(10).join(f"- {s['title']} ({s.get('url', 'N/A')})" for s in critique.conflicting_sources)}

Synthesis: {critique.synthesis}
"""
        else:
            self.thoughts.analyze("No external validation available")
        
        # Prepare prompt
        user_prompt = SYNTHESIZER_USER_PROMPT.format(
            analysis=analysis_text,
            critique=critique_text
        )
        
        self.thoughts.decide("Generate comprehensive report", 
                           "Combining internal analysis with external validation")
        
        try:
            # Call LLM
            self.thoughts.step("Report Generation", "Creating final markdown report")
            message = self._call_llm(SYNTHESIZER_SYSTEM_PROMPT, user_prompt)
            final_report = message.content[0].text
            
            self.logger.info(f"Generated report of {len(final_report)} characters")
            self.thoughts.success(f"Report generated: {len(final_report)} characters")
            self.thoughts.insight(f"Report sections: {final_report.count('#')} headers")
            return final_report
            
        except Exception as e:
            self.logger.error(f"Failed to synthesize report: {e}")
            self.thoughts.error(f"Report synthesis failed: {str(e)}", "Returning basic report format")
            # Return a basic report on error
            return f"""# Research Paper Analysis Report

## Summary
An error occurred during synthesis. Below is the raw analysis data:

## Analysis Results
{analysis_text}

## External Validation
{critique_text}

## Error Details
Failed to generate comprehensive report: {str(e)}
"""
