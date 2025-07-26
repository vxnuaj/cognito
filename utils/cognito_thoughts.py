"""
CognitoThoughts - A custom logging utility for agent thoughts and reasoning.
Designed for CLI streaming and real-time visibility into agent decision-making.
"""
import os
from datetime import datetime
from typing import Optional
import threading


class CognitoThoughts:
    """
    Custom logger for agent thoughts that writes to both console and a centralized file.
    Each log entry is labeled with the agent name for identification.
    """
    
    # Class-level lock for thread-safe file writing
    _file_lock = threading.Lock()
    
    # Centralized thoughts file
    THOUGHTS_FILE = "logs/cognito_thoughts.txt"
    
    def __init__(self, agent_name: str = "System"):
        """
        Initialize thoughts logger with agent name.
        
        Args:
            agent_name: Name of the agent for labeling thoughts
        """
        self.agent_name = agent_name
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.THOUGHTS_FILE), exist_ok=True)
        
        # Color codes for console output - now by agent instead of action
        self.agent_colors = {
            'System': '\033[95m',           # Purple
            'Orchestrator': '\033[93m',     # Yellow
            'ExtractorAgent': '\033[92m',   # Green
            'AnalystAgent': '\033[94m',     # Blue
            'SynthesizerAgent': '\033[96m', # Cyan
            'CriticAgent': '\033[91m',      # Red
            'default': '\033[97m'           # White
        }
        self.reset_color = '\033[0m'
        
        # Get color for this agent (check if agent name contains known agent types)
        self.agent_color = self.agent_colors.get('default')
        for agent_type, color in self.agent_colors.items():
            if agent_type in self.agent_name:
                self.agent_color = color
                break
    
    def _format_message(self, level: str, message: str, context: Optional[str] = None) -> str:
        """Format message with timestamp, agent name, and level."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Build the formatted message
        if context:
            return f"[{timestamp}] [{self.agent_name}] {level}: {message} | Context: {context}"
        else:
            return f"[{timestamp}] [{self.agent_name}] {level}: {message}"
    
    def _write_to_file(self, formatted_message: str):
        """Write message to centralized file with thread safety."""
        with self._file_lock:
            with open(self.THOUGHTS_FILE, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
                f.flush()  # Immediate flush for real-time streaming
    
    def _log(self, level: str, message: str, context: Optional[str] = None):
        """Base logging method."""
        formatted_msg = self._format_message(level, message, context)
        
        # Write to file
        self._write_to_file(formatted_msg)
        
        # Print to console with colored agent tag only
        colored_tag = f"{self.agent_color}[{self.agent_name} | {level}]{self.reset_color}"
        console_msg = f"{colored_tag} {message}"
        if context:
            console_msg += f" | {context}"
        print(console_msg)
    
    def think(self, thought: str, context: Optional[str] = None):
        """Log a general thought or observation."""
        self._log("THINK", thought, context)
    
    def step(self, step_name: str, details: str):
        """Log a step in the process."""
        self._log("STEP", f"{step_name}: {details}")
    
    def analyze(self, analysis: str):
        """Log an analysis or observation."""
        self._log("ANALYZE", analysis)
    
    def decide(self, decision: str, reasoning: str):
        """Log a decision point."""
        self._log("DECIDE", f"{decision} - {reasoning}")
    
    def error(self, error: str, context: Optional[str] = None):
        """Log an error or issue."""
        self._log("ERROR", error, context)
    
    def success(self, achievement: str):
        """Log a successful completion."""
        self._log("SUCCESS", achievement)
    
    def question(self, question: str):
        """Log a question or uncertainty."""
        self._log("QUESTION", question)
    
    def insight(self, insight: str):
        """Log a key insight or finding."""
        self._log("INSIGHT", insight)
    
    def progress(self, current: int, total: int, task: str):
        """Log progress on a task."""
        percentage = (current / total * 100) if total > 0 else 0
        self._log("PROGRESS", f"{task}: {current}/{total} ({percentage:.1f}%)")
    
    @classmethod
    def get_thoughts_file(cls) -> str:
        """Get the path to the centralized thoughts file."""
        return cls.THOUGHTS_FILE


# Create a singleton instance for system-level thoughts
system_thoughts = CognitoThoughts("System")
