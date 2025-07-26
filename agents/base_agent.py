"""Base agent class with common functionality for all agents."""
import anthropic
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from config import ANTHROPIC_API_KEY, LLM_MODEL_NAME
from utils.retry_utils import retry_with_exponential_backoff
from utils.cognito_thoughts import CognitoThoughts


class BaseAgent(ABC):
    """Base class for all agents with common LLM functionality."""
    
    def __init__(self, agent_name: str = "BaseAgent"):
        """Initialize base agent with common functionality."""
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
            
        self.agent_name = agent_name
        
        # Standard logger for technical logs
        self.logger = logging.getLogger(agent_name)
        
        # Initialize thoughts logger with agent name only (uses centralized file)
        self.thoughts = CognitoThoughts(agent_name=agent_name)
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = LLM_MODEL_NAME
        
        self.logger.info(f"{agent_name} initialized with model: {self.model}")
    
    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=2.0,
        exceptions=(anthropic.APIError, anthropic.APIConnectionError, anthropic.RateLimitError)
    )
    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> anthropic.types.Message:
        """
        Call the LLM with retry logic.
        
        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            max_tokens: Maximum tokens for response
            
        Returns:
            LLM response message
        """
        self.thoughts.step("Calling LLM", f"max_tokens={max_tokens}")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        self.thoughts.success(f"LLM responded with {len(response.content[0].text)} characters")
        return response
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Main execution method - must be implemented by subclasses."""
        pass
        
    def __del__(self):
        """Cleanup when agent is destroyed."""
        # No need to close thoughts logger as it uses centralized file
        pass
