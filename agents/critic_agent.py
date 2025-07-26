import anthropic
import os
import logging
import json
import time
from pydantic import BaseModel

from utils.shared_types import AnalysisResult, Critique
from config import ANTHROPIC_API_KEY, LLM_MODEL_NAME
from orgo import Computer
from gui_agents.s2.agents.agent_s import AgentS2
from gui_agents.s2.agents.grounding import OSWorldACI

class RemoteExecutor:
    def __init__(self):
        self.computer = Computer()
        self.platform = "linux" # Orgo VMs typically run Linux
    
    def screenshot(self):
        return self.computer.screenshot_base64()
    
    def exec(self, code):
        result = self.computer.exec(code)
        if not result['success']:
            raise Exception(result.get('error', 'Execution failed'))
        if result['output']:
            logging.info(f"Executor Output: {result['output']}")
    
    def destroy(self):
        self.computer.destroy()

class CriticAgent:
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.executor = RemoteExecutor()
        
        # Initialize AgentS2
        engine_params = {"engine_type": "anthropic", "model": LLM_MODEL_NAME}
        grounding_params = {"engine_type": "anthropic", "model": LLM_MODEL_NAME} # Using same model for simplicity
        
        self.grounding_agent = OSWorldACI(
            platform=self.executor.platform,
            engine_params_for_generation=engine_params,
            engine_params_for_grounding=grounding_params
        )
        
        self.agent_s2 = AgentS2(
            engine_params=engine_params,
            grounding_agent=self.grounding_agent,
            platform=self.executor.platform,
            action_space="pyautogui", # AgentS2 uses pyautogui actions
            observation_type="screenshot"
        )

    def run(self, analysis: AnalysisResult) -> Critique:
        logging.info(f"CriticAgent: Evaluating analysis for {analysis.metadata.title}")
        
        corroborating_sources = []
        conflicting_sources = []
        synthesis_text = ""

        try:
            for claim in analysis.key_claims:
                instruction = f"Search for research papers related to \"{claim}\" and summarize findings that either support or contradict this claim. Provide URLs."
                logging.info(f"CriticAgent: Instructing AgentS2: {instruction}")
                
                # Enhanced multi-step Agent S2 task loop
                max_steps = 5  # Allow up to 5 steps for each search task
                step_count = 0
                task_complete = False
                
                while step_count < max_steps and not task_complete:
                    step_count += 1
                    logging.info(f"Step {step_count}/{max_steps} for claim: {claim}")
                    
                    obs = {"screenshot": self.executor.screenshot()}
                    
                    # Get Agent S2 prediction
                    info, action = self.agent_s2.predict(
                        instruction=instruction if step_count == 1 else None,  # Only provide instruction on first step
                        observation=obs
                    )
                    
                    if info:
                        logging.info(f"AgentS2 Info: {info}")
                        # Check if task is marked as complete
                        if "task complete" in info.lower() or "done" in info.lower():
                            task_complete = True
                    
                    if action and action[0] and not task_complete:
                        try:
                            logging.info(f"CriticAgent: Executing AgentS2 action: {action[0]}")
                            self.executor.exec(action[0])
                            time.sleep(2)  # Give time for action to complete
                        except Exception as action_error:
                            logging.error(f"Error executing action: {action_error}")
                            # Continue to next step despite error
                    else:
                        # No action provided, assume task is complete
                        task_complete = True
                
                # After task loop completes, analyze final state
                final_obs = {"screenshot": self.executor.screenshot()}
                summary_prompt = f"""
                Based on the current screenshot after searching for information about: '{claim}',
                summarize any findings that corroborate or conflict with this claim.
                Extract relevant paper titles, authors, and URLs visible on screen.
                
                Format your response as a JSON object with:
                - 'corroborating' (list of dicts with 'title', 'url', and optionally 'authors')
                - 'conflicting' (list of dicts with 'title', 'url', and optionally 'authors')  
                - 'synthesis' (string summary of findings)
                
                If no relevant information is visible, return empty lists.
                """
                
                try:
                    message = self.client.messages.create(
                        model=LLM_MODEL_NAME,
                        max_tokens=1000,
                        system="You are an AI assistant that analyzes screenshots of academic search results and research papers.",
                        messages=[
                            {"role": "user", "content": summary_prompt,
                             "images": [{"type": "base64", "media_type": "image/png", "data": final_obs["screenshot"]}]}
                        ]
                    )
                    llm_response = message.content[0].text
                    parsed_response = json.loads(llm_response)

                    corroborating_sources.extend(parsed_response.get("corroborating", []))
                    conflicting_sources.extend(parsed_response.get("conflicting", []))
                    synthesis_text += f"\nAnalysis for claim \"{claim}\": {parsed_response.get('synthesis', '')}"

                except Exception as e:
                    logging.error(f"CriticAgent: Error processing results for claim \"{claim}\": {e}")
                    synthesis_text += f"\nCould not analyze search results for claim \"{claim}\" due to an error."

            return Critique(
                corroborating_sources=corroborating_sources,
                conflicting_sources=conflicting_sources,
                synthesis=synthesis_text.strip()
            )
        except Exception as e:
            logging.error(f"CriticAgent: An error occurred during AgentS2 interaction: {e}")
            return Critique(
                corroborating_sources=[],
                conflicting_sources=[],
                synthesis=f"Error during external validation: {e}"
            )
        finally:
            self.executor.destroy() # Ensure the computer is destroyed

class Critique(BaseModel):
    corroborating_sources: list
    conflicting_sources: list
    synthesis: str
