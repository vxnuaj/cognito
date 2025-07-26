"""Analyst Agent - Provides expert analysis from different personas."""
import logging
import json

from agents.base_agent import BaseAgent
from agents.prompts import get_analyst_system_prompt, ANALYST_USER_PROMPT, PERSONAS
from utils.shared_types import StructuredContent, AnalysisResult


class AnalystAgent(BaseAgent):
    """Agent that analyzes research papers from a specific persona perspective."""
    
    def __init__(self, persona: str = None):
        """Initialize with optional persona."""
        super().__init__(f"AnalystAgent-{persona or 'Default'}")
        self.persona = persona or PERSONAS[0]
        
    def run(self, structured_content: StructuredContent) -> AnalysisResult:
        """Analyze the structured content and return analysis results."""
        self.logger.info(f"Analyzing paper with persona: {self.persona}")
        self.thoughts.step("Starting Analysis", f"Persona: {self.persona}")
        self.thoughts.analyze(f"Content sections - Abstract: {len(structured_content.abstract)} chars, "
                           f"Intro: {len(structured_content.introduction)} chars")
        
        # Prepare prompts
        system_prompt = get_analyst_system_prompt(self.persona)
        user_prompt = ANALYST_USER_PROMPT.format(
            title="Research Paper Analysis",
            abstract=structured_content.abstract,
            introduction=structured_content.introduction,
            methodology=structured_content.methodology,
            results=structured_content.results,
            conclusion=structured_content.conclusion,
            persona=self.persona
        )
        
        self.thoughts.decide(f"Analyze as {self.persona}", 
                           "Each persona provides unique perspective on the research")
        
        try:
            # Call LLM with retry logic
            self.thoughts.step("LLM Analysis", "Sending content for expert review")
            message = self._call_llm(system_prompt, user_prompt)
            response_text = message.content[0].text
            
            # Parse response with Pydantic
            self.thoughts.step("Parsing Analysis", "Extracting structured insights")
            result = AnalysisResult.model_validate_json(response_text)
            
            self.logger.info(f"Analysis complete - found {len(result.key_claims)} key claims")
            self.thoughts.success(f"Analysis complete: {len(result.key_claims)} claims identified")
            
            # Log key insights
            if result.key_claims:
                self.thoughts.insight(f"Top claim: {result.key_claims[0][:100]}...")
            if result.metrics_and_results:
                self.thoughts.analyze(f"Found {len(result.metrics_and_results)} metrics/results")
            if result.tldr:
                self.thoughts.insight(f"TL;DR: {result.tldr[:150]}...")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            self.thoughts.error(f"Analysis failed: {str(e)}", 
                              f"Persona: {self.persona}, Content length: {len(str(structured_content))}")
            # Return minimal valid result on error
            return AnalysisResult(
                key_claims=["Analysis failed due to error"],
                metrics_and_results={},
                methodology_summary="Error during analysis",
                mathematical_derivations=[],
                tldr="Analysis could not be completed",
                eli5="There was a problem analyzing this paper"
            )
