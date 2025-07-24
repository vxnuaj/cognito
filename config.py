import os
from dotenv import load_dotenv

load_dotenv()

# Default values for the application
DEFAULT_NUM_PAPERS = 1
DEFAULT_NUM_VMS = 1

# ArXiv API settings (if needed, though arxiv library handles most)
ARXIV_API_URL = "http://export.arxiv.org/api/query?"

# Paths
OUTPUT_DIR = "output"
TEMP_DIR = "temp"

# Orgo and LLM API keys
ORGO_API_KEY = os.getenv("ORGO_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# LLM settings for summarization (if direct LLM calls are made outside of Orgo Model Agent)
LLM_MODEL_NAME = "claude-3-5-haiku-20241022" 
